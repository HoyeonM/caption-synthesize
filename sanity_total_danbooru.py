import os
import json
import gradio as gr
from PIL import Image
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import argparse
import concurrent.futures
import tqdm


def list_files_in_directory(directory_path):
    files_list = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
    return files_list

def sanity_check(tags, captions):

    tags = tags.split('\n')
    tags = [t.split(':', 1)[-1] for t in tags]
    tags = [t for t in tags if t]
    tags = [t.replace('_', ' ').replace('-', ' ') for ts in tags for t in ts.split(' ')]
    captions = [caption.replace('_', ' ').replace('-',' ') for caption in captions]
    tags_not_in_captions = [t for t in tags if all(t.lower() not in caption.lower() for caption in captions)]

    return tags_not_in_captions
   

def load_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            file_contents = file.read()
            return json.loads(file_contents)
    except FileNotFoundError:
        print(f"파일 '{file_path}'를 찾을 수 없습니다.")
    except Exception as e:
        print(f"파일을 열 때 오류가 발생했습니다: {e}")

def load_gemini_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"파일 '{file_path}'를 찾을 수 없습니다.")
    except Exception as e:
        print(f"파일을 열 때 오류가 발생했습니다: {e}")

def process_gemini_files(folder_path):
    files_list = list_files_in_directory(folder_path)
    result_list = []

    for filename in files_list:
        result = filename.rsplit('.', 1)[0]
        if '_' in result:
            result = result.rsplit('_', 1)[0]

        result_list.append(result)

    result_list = list(set(result_list))
    result_list = [item for item in result_list if item]

    return result_list

def process_gemini_data(folder_path, image_name):
    matching_files = [filename for filename in os.listdir(folder_path) if image_name in filename]
    file_contents_list = [] 

    for j in matching_files:
        if "gemini" in j and j.endswith(".txt"): 
            gemini_data = load_gemini_file(os.path.join(folder_path, j))
            if gemini_data:
                file_contents_list.append(gemini_data)
        elif "gemini" not in j and j.endswith(".txt"):
            tag = load_gemini_file(os.path.join(folder_path, j))
            
            
    if len(file_contents_list) == 0:
        pass
    else:
        return {
            'image_name': image_name,
            'tag': tag,
            'captions': file_contents_list,
            'sanity_check':sanity_check(tag, file_contents_list),
            'sanity_check_count' : len(sanity_check(tag, file_contents_list))
        }

def create_json_file(create_json_path, data):
    json_file_path = os.path.join(create_json_path, data['image_name'] + '_total' + '.json')

    try:
        with open(json_file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
      #  print(f"JSON 파일이 성공적으로 생성되었습니다: {json_file_path}")
    except Exception as e:
        print(f"JSON 파일 생성 중 오류가 발생했습니다: {e}")

def process_gemini_data_parallel(args):
    folder_path, image_name = args
    return process_gemini_data(folder_path, image_name)

def main_parallel(folder_path, create_json_path):
    result_list = process_gemini_files(folder_path)

    # ThreadPoolExecutor를 사용하여 병렬로 작업을 수행합니다.
    with concurrent.futures.ThreadPoolExecutor() as executor:
        args_list = [(folder_path, image_name) for image_name in result_list]
        results = list(tqdm.tqdm(executor.map(process_gemini_data_parallel, args_list), total=len(args_list)))

    # 생성된 JSON 파일을 저장합니다.
    for data in results:
        create_json_file(create_json_path, data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process gemini files and create JSON files with sanity_check.')
    parser.add_argument('--folder_path', type=str, default="/data0/DanbooruSubset-Multiples-30-2", help='Path to the folder containing gemini files.')
    parser.add_argument('--create_json_path', type=str, default="/data0/scripts/mina/output/two-basic-sanity", help='Path to store the generated JSON files with sanity_check.')
    args = parser.parse_args()

    if not args.folder_path or not args.create_json_path:
        print("Please provide both --folder_path and --create_json_path.")
    else:
        main_parallel(args.folder_path, args.create_json_path)
