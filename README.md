# Representing, optimizing and evolving matrix product states on NISQ devices

## Installation
Clone this somewhere. Run `pip install -e .` from this folder.

### Developement

If you want to develop this project or run python notebooks on your machine,
you have to install other required packages.

This project uses [pipenv](https://pipenv.pypa.io/en/latest/) to manage the required
packages. Please follow the instructions on the [official document](https://pipenv.pypa.io/en/latest/)
or execute the command below to install pipenv first.

```
pip install pipenv
```

Next step, please active a virtual environment by

```
pipenv shell
```

and install all required packages by

```
pipenv install
```

## Folder Structure

```bash
{root}/
├─ node_modules/
├─ circuits/ # This is author's qpic playground. There is no useful thing under this folder.
│  ├─ images/ # output images
│  └─ qpic_circuits/ # a clone of https://github.com/qpic/qpic
└─ README.md
```
 
 
