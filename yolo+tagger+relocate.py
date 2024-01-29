
from PIL import Image
import argparse
from concurrent.futures import ThreadPoolExecutor
import pathlib
import os


def main(original_image_path, segmented_image_path):
    original_general_tags = {}
    # EXTRACT GENERAL TAGS FROM ORIGINAL IMAGES
    for filename in os.listdir(original_image_path):
        original_image_name = os.path.splitext(filename)[0]
        # import pdb; pdb.set_trace()
        if filename.endswith('.txt'):
            image_name = os.path.splitext(filename)[0]
            tags_file_path = os.path.join(original_image_path, filename)
            original_general_tags[image_name] = extract_general_tags(tags_file_path)
    
            # PROCESS SEGMENTED IMAGES
            segmented_info = process_segmented_image(original_image_name, segmented_image_path)
            # SORT SEGMENTS BY HORIZONTAL CENTER AND GROUP TAGS
            relocated_tags_line = sort_and_group_tags(segmented_info, original_general_tags.get(image_name, []))
        
            # Save the relocated tags as new txt files
            original_tags_file_path = os.path.join(original_image_path, f'{image_name}.txt')
            save_path = os.path.join(original_image_path, f'{image_name}_relocated.txt')
            save_relocated_tags(save_path, open(original_tags_file_path, 'r').readlines(), relocated_tags_line)
    
  
def sort_and_group_tags(segmented_info, original_tags):
    # Sort segments by horizontal center
    sorted_segments = sorted(segmented_info.items(), key=lambda x: get_horizontal_center(x[1]['coords']) if x[1]['coords'] else float('inf'))
    
    # Group the general tags by segment and order them from left to right
    matched_tag_list = []
    for segment_id, segment in sorted_segments:
        if 'tags' in segment:
            common_tags = [tag for tag in original_tags if tag in segment['tags']]
            matched_tag_list.append(common_tags)
            
    flattened_matched_tags = [tag for sublist in matched_tag_list for tag in sublist]
    remaining_tags = [tag for tag in original_tags if tag not in flattened_matched_tags]
    # replace space in tag with '_'
    remaining_tags = [tag.replace(' ', '_') for tag in remaining_tags]
    
    # replace space in tag with '_' in matched_tag_list
    matched_tag_list = [[tag.replace(' ', '_') for tag in tags] for tags in matched_tag_list]
    
    relocated_tags = ' ||| '.join([' '.join(tags) for tags in matched_tag_list])
    relocated_tags = ' '.join(remaining_tags)+(' ||| ' + relocated_tags if relocated_tags else '')
    import pdb; pdb.set_trace()
    return relocated_tags
  
def normalize_tags(tags):
    """Normalizes tags by replacing underscores with spaces."""
    return [tag.replace('_', ' ') for tag in tags]  

def extract_general_tags(tags_file):   
    """Extracts general tags from the given tags file."""
    with open(tags_file, 'r') as file:
        content = file.read().strip()
        general_tags_line = next((line for line in content.split('\n') if 'GENERAL TAGS:' in line), None)
        if general_tags_line:
            return normalize_tags(general_tags_line.replace('GENERAL TAGS:', '').strip().split(' '))
    return []


def process_coordinates(coords_file):
    """Extracts coordinates from the given coordinates file."""
    with open(coords_file, 'r') as file:
        coords = file.read().strip().split(' ')
        return tuple(map(float, coords))
    
    
def process_segmented_image(original_image, segmented_image_path):
    """Processes the segmented image and returns the cropped images."""
    # while filename in segmented_image_path has 'original_image' in it:
    #   process the image
    segmented_info = {}
    for filename in os.listdir(segmented_image_path):
        if not filename.startswith(original_image + '_'):
            continue
        
        base_name, extension = os.path.splitext(filename)
        image_id, segment_id = base_name.split('_')[:2]
        segment_key = f"{image_id}_{segment_id}"
        if segment_key not in segmented_info:
            segmented_info[segment_key] = {'coords': None, 'tags': []}
            
        if filename.endswith('_coords.txt'):
            coords = process_coordinates(os.path.join(segmented_image_path, filename))
            segmented_info[segment_key]['coords'] = coords

        elif filename.endswith('.txt') and not filename.endswith('_coords.txt'):
            tags = process_tags(os.path.join(segmented_image_path, filename))
            segmented_info[segment_key]['tags'] = tags
    
    return segmented_info


def process_tags(tags_file):
    with open(tags_file, 'r') as file:
        tags = file.read().strip()
        tags = tags.strip("[]").replace("'", "").split(', ')
        return tags

def get_horizontal_center(coords):
    """Returns the horizontal center of the given coordinates."""
    x1, _, x2, _ = coords
    return (x1 + x2) / 2  

def save_relocated_tags(save_path, original_tag_lines, relocated_tag_lines):
    """Saves the relocated tags as a new txt file."""
    with open(save_path, 'w') as file:
        for line in original_tag_lines:
            if 'GENERAL TAGS:' in line:
                file.write('GENERAL TAGS: ' + relocated_tag_lines + '\n')
            else:
                file.write(line)
             
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--original_image_path', type=str, default='test2-yolo-subset', help='original image path')
    parser.add_argument('--segmented-image-path', type=str, default='test2-yolo-subset-save', help='segmented image path')
    parser.add_argument('--save-dir', type=str, default='/data/dataset_cropped', help='directory to save new txt file')

    args = parser.parse_args()
    original_image_path = args.original_image_path
    segmented_image_path = args.segmented_image_path
    main(original_image_path, segmented_image_path)
        