import cirq 
from qmps.ground_state import Hamiltonian
from xmps.spin import paulis, U4, swap
import numpy as np
import numpy.random as ra
from qmps.ground_state import Hamiltonian
from qmps.represent import get_env_exact, State, FullStateTensor, FullEnvironment
from qmps.represent import ShallowStateTensor, split_2s, ShallowCNOTStateTensor
from qmps.represent import ShallowFullStateTensor
import math
import matplotlib.pyplot as plt
import matplotlib as mpl
from functools import reduce
from scipy.optimize import minimize_scalar
from tqdm import tqdm
from xmps.tensor import partial_trace
from scipy.linalg import expm
mpl.style.use('pub_fast')
X, Y, Z = paulis(0.5)
π = np.pi

def gate(v):
    return ShallowFullStateTensor(2, v)

def evo_state(params, which, old_params, H, dt):
    assert len(params)==30
    p2, p1 = np.split(params, 2)
    p2_, p1_ = np.split(old_params, 2)
    if which=='energy':
        qbs = cirq.LineQubit.range(4)
        C = cirq.Circuit([gate(p1_)(*qbs[2:]),
                                   gate(p2_)(*qbs[1:3]),
                                   gate(p2_)(*qbs[:2]), 
                                   FullStateTensor(expm(-1j*H*dt/2))(*qbs[1:3]),
                                   cirq.inverse(gate(p2))(*qbs[:2]),
                                   cirq.inverse(gate(p2))(*qbs[1:3]),
                                   cirq.inverse(gate(p1))(*qbs[2:])])
        s = cirq.Simulator()
        return s.simulate(C).final_state
    elif which=='v_purity':
        qbs = [[cirq.GridQubit(y, x) for x in range(2)] 
                for y in range(2)]
        C = cirq.Circuit([gate(p1)(*qbs[0][:2]),
                                   gate(p1)(*qbs[1][:2]), 
                                   cirq.SWAP(*qbs[0][:2])])
        s = cirq.Simulator()
        return s.simulate(C).final_state
    elif which=='u_purity':
        qbs = [[cirq.GridQubit(y, x) for x in range(3)]
                for y in range(2)]
        C = cirq.Circuit([gate(p1)(*qbs[0][1:]), 
                                   gate(p2)(*qbs[0][:2]),
                                   gate(p1)(*qbs[1][1:]), 
                                   gate(p2)(*qbs[1][:2]), 
                                   cirq.SWAP(*qbs[0][:2]), 
                                   cirq.SWAP(*qbs[0][1:])])
        s = cirq.Simulator()
        return s.simulate(C).final_state
    elif which=='uv_purity':
        qbs = cirq.LineQubit.range(5)
        C = cirq.Circuit([gate(p1)(*qbs[3:]), 
                                   gate(p2)(*qbs[2:4]), 
                                   gate(p1)(*qbs[:2]), 
                                   cirq.SWAP(*qbs[:2])])
        s = cirq.Simulator()
        return s.simulate(C).final_state
    
def op_state(params, which='energy'):
    assert len(params)==30
    p2, p1 = np.split(params, 2)
    if which=='energy':
        qbs = cirq.LineQubit.range(4)
        C = cirq.Circuit([gate(p1)(*qbs[2:]),
                                   gate(p2)(*qbs[1:3]),
                                   gate(p2)(*qbs[:2])])
        s = cirq.Simulator()
        return s.simulate(C).final_state
    elif which=='v_purity':
        qbs = [[cirq.GridQubit(y, x) for x in range(2)] 
                for y in range(2)]
        C = cirq.Circuit([gate(p1)(*qbs[0][:2]),
                                   gate(p1)(*qbs[1][:2]), 
                                   cirq.SWAP(*qbs[0][:2])])
        s = cirq.Simulator()
        return s.simulate(C).final_state
    elif which=='u_purity':
        qbs = [[cirq.GridQubit(y, x) for x in range(3)]
                for y in range(2)]
        C = cirq.Circuit([gate(p1)(*qbs[0][1:]), 
                                   gate(p2)(*qbs[0][:2]),
                                   gate(p1)(*qbs[1][1:]), 
                                   gate(p2)(*qbs[1][:2]), 
                                   cirq.SWAP(*qbs[0][:2]), 
                                   cirq.SWAP(*qbs[0][1:])])
        s = cirq.Simulator()
        return s.simulate(C).final_state
    elif which=='uv_purity':
        qbs = cirq.LineQubit.range(5)
        C = cirq.Circuit([gate(p1)(*qbs[3:]), 
                                   gate(p2)(*qbs[2:4]), 
                                   gate(p1)(*qbs[:2]), 
                                   cirq.SWAP(*qbs[:2])])
        s = cirq.Simulator()
        return s.simulate(C).final_state

def evo_H():
    return -np.diag(np.eye(16)[0])

def op_H(H):
    #H = np.eye(4)
    return reduce(np.kron, [np.eye(2), H, np.eye(2)])

def swapper():
    return -np.kron(np.kron(np.eye(2), swap()), np.eye(8))

def sinusoids(H, state_function, parameters, args=()): 
    def ϵ(x):
        return np.real(state_function(x, *args).conj().T@H@state_function(x, *args))
    I = np.eye(len(parameters))
    xs = np.linspace(-π, π, 101)
    for i in range(15):
        es = []
        for x in xs:
            es.append(ϵ(parameters+x*I[i]))
        θ_ = (-π/2-np.arctan2(2*ϵ(parameters)-ϵ(parameters+I[i]*π/2)-ϵ(parameters-I[i]*π/2), ϵ(parameters+I[i]*π/2)-ϵ(parameters-I[i]*π/2)))
        θ = np.arctan2(np.sin(θ_), np.cos(θ_))
        plt.scatter([θ], [ϵ(parameters+θ*I[i])], marker='x')

        plt.plot(xs, es)
    plt.show()

def double_sinusoids(H, state_function, parameters, args=()): 
    def ϵ(x):
        uv_state, u_state, v_state, e_state = (state_function(x, 'uv_purity', *args), 
                                               state_function(x, 'u_purity', *args), 
                                               state_function(x, 'v_purity', *args), 
                                               state_function(x, 'energy', *args))
        v_purity = np.real(v_state.conj().T@np.kron(np.eye(2), np.kron(swap(), np.eye(2)))@v_state)
        u_purity = np.real(u_state.conj().T@np.kron(np.eye(4), np.kron(swap(), np.eye(4)))@u_state)
        uv_purity = np.real(uv_state.conj().T@np.kron(np.kron(np.eye(2), swap()), np.eye(4))@uv_state)
        energy = np.real(e_state.conj().T@H@e_state) 
        k = 1
        return energy,+k*u_purity,+k*v_purity,-2*k*uv_purity

    I = np.eye(len(parameters))
    xs = np.linspace(-π, π, 101)
    for i in range(15):
        es = []
        def M(x):
            return np.sum(ϵ(parameters+I[i]*x))
        for x in xs:
            es.append(M(x))

        A = float((M(0)+M(np.pi)))
        B = float((M(0)-M(np.pi)))
        C = float((M(np.pi/2)+M(-np.pi/2)))
        D = float((M(np.pi/2)-M(-np.pi/2)))
        E = float((M(np.pi/4)-M(-np.pi/4)))

        a, b, c, d = 1/4*(2*E-np.sqrt(2)*D), 1/4*(A-C), 1/2*D, 1/2*B

        P = np.sqrt(a**2+b**2)
        u = np.arctan2(b, a)
        
        Q = np.sqrt(c**2+d**2)
        v = np.arctan2(d, c)

        def f(x): return (P*np.sin(2*x+u)+Q*np.sin(x+v))

        plt.scatter(xs, f(xs)-f(xs)[0]+es[0], s=10)
        def wrap(x):
            return np.arctan2(np.sin(x), np.cos(x))
        θ = wrap(minimize_scalar(f, bounds = [-np.pi, np.pi]).x)
        plt.scatter([θ], [M(θ)], marker='x')
        plt.plot(xs, es)
    plt.show()


def rotosolve(H, state_function, initial_parameters, args=(), N_iters=10):
    """rotosolve

    :param H: hamiltonian.
    :param state_function: function taking parameters and returning complex vector.
    :param initial_parameters: initial parameters.
    :param args: extra arguments to state_function.
    :param N_iters: maximum number of optimization iterations.
    """
    S = []
    es = []
    I = np.eye(len(initial_parameters))
    params = initial_parameters
    for _ in range(N_iters):
        #H = Hamiltonian({'ZZ': 1, 'X': 0.5}).to_matrix()

        def ϵ(x):
            return np.real(state_function(x, *args).conj().T@H@state_function(x, *args))

        for i, _ in enumerate(params):
            θ_ = (-np.pi/2-np.arctan2(2*ϵ(params)-ϵ(params+I[i]*π/2)-ϵ(params-I[i]*π/2), ϵ(params+I[i]*π/2)-ϵ(params-I[i]*π/2)))
            params[i] += np.arctan2(np.sin(θ_), np.cos(θ_))
            params[i] = np.arctan2(np.sin(params[i]), np.cos(params[i]))
        sinusoids(H, state_function, params)
        es.append(ϵ(params))
        S.append(params.copy())
    return es, S

def double_rotosolve(H, state_function, initial_parameters, args=(), N_iters=5):
    """rotosolve

    :param H: hamiltonian.
    :param state_function: function taking parameters and returning complex vector.
    :param initial_parameters: initial parameters.
    :param args: extra arguments to state_function.
    :param N_iters: maximum number of optimization iterations.
    """
    S = []
    ss = []
    es = []
    I = np.eye(len(initial_parameters))
    params = initial_parameters
    for w in range(N_iters):
        print(w, ', ', sep='', end='', flush=True)
        #H = Hamiltonian({'ZZ': 1, 'X': 0.5}).to_matrix()

        def ϵ(x):
            uv_state, u_state, v_state, e_state = (state_function(x, 'uv_purity', *args), 
                                                   state_function(x, 'u_purity', *args), 
                                                   state_function(x, 'v_purity', *args), 
                                                   state_function(x, 'energy', *args))
            v_purity = np.real(v_state.conj().T@np.kron(np.eye(2), np.kron(swap(), np.eye(2)))@v_state)
            u_purity = np.real(u_state.conj().T@np.kron(np.eye(4), np.kron(swap(), np.eye(4)))@u_state)
            uv_purity = np.real(uv_state.conj().T@np.kron(np.kron(np.eye(2), swap()), np.eye(4))@uv_state)
            energy = np.real(e_state.conj().T@H@e_state) 

            k = 1
            return energy,+k*u_purity,+k*v_purity,-2*k*uv_purity


        for i, _ in tqdm(enumerate(params)):
            #print(i, ', ', end='', sep='', flush=True)
            def M(x):
                return np.sum(ϵ(params+I[i]*x))

            A = (M(0)+M(np.pi))
            B = (M(0)-M(np.pi))
            C = (M(np.pi/2)+M(-np.pi/2))
            D = (M(np.pi/2)-M(-np.pi/2))
            E = (M(np.pi/4)-M(-np.pi/4))

            a, b, c, d = 1/4*(2*E-np.sqrt(2)*D), 1/4*(A-C), 1/2*D, 1/2*B

            P = np.sqrt(a**2+b**2)
            u = np.arctan2(b, a)
            
            Q = np.sqrt(c**2+d**2)
            v = np.arctan2(d, c)

            def f(x): return (P*np.sin(2*x+u)+Q*np.sin(x+v))

            θ_ = minimize_scalar(f, bounds = [-np.pi, np.pi]).x
            #θ_ = (-np.pi/2-np.arctan2(2*ϵ(params)-ϵ(params+I[i]*π/2)-ϵ(params-I[i]*π/2), ϵ(params+I[i]*π/2)-ϵ(params-I[i]*π/2)))
            params[i] += np.arctan2(np.sin(θ_), np.cos(θ_))
            #params[i] = np.arctan2(np.sin(params[i]), np.cos(params[i]))
        print('\n', sep='', end='', flush=True)
        #double_sinusoids(H, state_function, params)
        es.append(ϵ(params))
        print('\n', es[-1], es[-1][1]+es[-1][2]+es[-1][3], '\n', sep='', end='', flush=True)
    return params, np.array(es)

N=20
Ps = []
evs = []
for i in range(N):
    dt = 0.1# if i==0 else 0.01
    p_initial = np.random.randn(30)
    p_old = p_initial
    #evo_state(p, p_old, Hamiltonian({'ZZ':-1, 'X':2}).to_matrix(), dt=0.01, which='energy')
    p_, es = double_rotosolve(evo_H(), 
                          evo_state, 
                          p_initial, 
                          args=(p_old, Hamiltonian({'X':1}).to_matrix(), dt), 
                          N_iters=200)
                     
    
    Ps.append([p_, es])

    ZZ = np.kron(np.eye(2), np.kron(Z, np.eye(4)))
    ψ = op_state(p_)
    evs.append(ψ.conj().T@ZZ@ψ)
    print(evs)

    p_initial = p_old = p_
    print(es)
np.save('params_energies', np.array(Ps)) 
plt.plot(evs)
plt.show()
