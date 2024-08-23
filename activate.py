import argparse
from ruamel.yaml import YAML
from pathlib import Path
from collections import defaultdict
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description='Combine YAML files into a single metrics.yaml file.')
    parser.add_argument('--discovery_dir', default='.',
                        help='Directory to search for YAML files (default: current directory)')
    parser.add_argument('--prepend_tags', type=str, default='', nargs='+',
                        help='prepend this comma separated set of tags to the metric path')
    parser.add_argument('--input_file', default=None)
    parser.add_argument('--metrics_file', default='metrics.yaml')
    parser.add_argument('--collisions_file', default='collisions.yaml')
    args = parser.parse_args()

    if args.input_file is None:
        discovery_dir = Path(args.discovery_dir)
        yaml_files = list(discovery_dir.glob('metrics.discovered.*.yaml'))
    else:
        yaml_files = Path(args.input_file)

    # preserve YAML file properties
    yaml = YAML()
    # yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    combined_data = []

    # read the discovery files
    for file in yaml_files:
        with open(file, 'r') as f:
            try:
                data = yaml.load(f)
                combined_data += data
            except yaml.YAMLError as e:
                print(f"Error reading {file}: {e}")

    # populate the collision map
    collision_map = defaultdict(list)
    for description in combined_data:
        discovered_name = description['match']['metric']['match']

        # source and name are always added to the segment by default, so add them
        source = description['sampleTags']['source'] if 'source' in description['sampleTags'] else ''
        name = description['sampleTags']['name'] if 'name' in description['sampleTags'] else source

        # add tags provided by command line to the key and also to the description yaml
        tag_to_prepend = []
        for tag in args.prepend_tags:
            if tag in description['sampleTags']:
                tag_to_prepend.append(description['sampleTags'][tag])
                description['metric']['resource'].insert(0, f"${{tag:{tag}}}")

        prepend_tags_str = '|'.join(tag_to_prepend)

        metric_path = source + '|' + name + '|' + prepend_tags_str + discovered_name
        collision_map[metric_path].append(description)

    # report the collisions
    print('*************************************')
    print('COLLISIONS')
    print('*************************************')

    unique_metric_path = []
    collisions = []

    for discovered_name in collision_map:
        num_collisions = len(collision_map[discovered_name])
        if num_collisions > 1:

            # get the tags that are common to all the metrics in the collision
            tags = [set(d['sampleTags'].keys()) for d in collision_map[discovered_name]]
            common_tags = set.intersection(*tags)

            # if common_tags in the collision have the same value, filter them out, they are not going to help us disambiguate
            disambiguating_tags = []
            for tag in common_tags:
                values = [description['sampleTags'][tag] for description in collision_map[discovered_name]]
                if len(set(values)) > 1:
                    disambiguating_tags.append(tag)

            print(f'{discovered_name}, disambiguating_tags: {disambiguating_tags}')

            for description in collision_map[discovered_name]:
                sample_tags = description['sampleTags']
                print(f'\t tags : {sample_tags}')

            # collisions.append({'collision': discovered_name, 'disambiguating_tags': disambiguating_tags})
            collisions += collision_map[discovered_name]

        else:
            # no collision, add to map
            unique_metric_path += collision_map[discovered_name]

    for description in unique_metric_path:
        description['enabled'] = 'true'

    print('*************************************')

    time = datetime.now()

    with open(f'metrics.yaml', 'w') as outfile:
        yaml.dump(unique_metric_path, outfile)

    with open(f'collisions.yaml', 'w') as outfile:
        yaml.dump(collisions, outfile)

    print(f"Found {len(collisions)} and added to collisions.yaml")
    print(f"Added {len(unique_metric_path)} discovered into metrics.yaml")


if __name__ == '__main__':
    main()
