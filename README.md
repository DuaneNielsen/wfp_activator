# Wavefront Proxy Activator

Script to convert Wavefront Proxy discovery files to active configuration

### Install instructs

Developed on python 3.8, so make sure you have 3.8+installed

Clone the repo

Install the requirements.txt

```
pip install -r requirements.txt
```

### To use

copy the activate.py file to the directory that contains your wavefront.metrics.discoveredX.yaml files and run the command

```
python3 activate.py
```

it may take some time to complete, be patient, it will output 2 files

collisions.yaml
metrics.yaml

collisions.yaml contains the metrics that conflict, they will need to have tags added to the metric name to resolve the conflicts
metrics.yaml should be good to promote

The script will write a list of tags that could disambiguate each of the collisions, choose the tags you want to use, and run the command again.

```
python3 activate.py --prepend_tags common_name pid 
```
