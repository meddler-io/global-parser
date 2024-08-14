import os
base_path = 'doc/content/en/integrations/parsers/file'
base_path = './'


def read_all_markdown_files(base_path):
    # Walk through the directory structure
    print("read_all_markdown_files", base_path)
    for root, dirs, files in os.walk(base_path):
        print("files", root )
        for file in files:
            if file.endswith('.md'):  # Check if the file is a markdown file
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f'File: {file_path}')
                        print(content)
                        print('---' * 10)  # Separator between files
                except Exception as e:
                    print(f'An error occurred while reading {file_path}: {e}')

# Define the base path

# Call the function to read and print all markdown files
read_all_markdown_files(base_path)
