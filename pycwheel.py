"""Compile all py files in a wheel to pyc files."""
import csv
import shutil
import glob
import os
import argparse
import compileall
import zipfile
import hashlib
import json
import base64


__version__ = "1.0.0"
__author__ = "Grant Patten <grant@gpatten.com>"

CHUNK_SIZE = 1024
HASH_TYPE = "sha256"


def convert_wheel(whl_file):
    """Generate a new whl with only pyc files.

    This whl will append .compiled to the version information.
    """

    whl_name, file_ext = os.path.splitext(whl_file)

    if file_ext != ".whl":
        raise TypeError("File to convert must be a *.whl")

    # Clean up leftover files
    shutil.rmtree(whl_name, ignore_errors=True)

    # Extract our zip file temporarily
    with zipfile.ZipFile(whl_file, "r") as whl_zip:
        whl_zip.extractall(whl_name)

    # Replace all py files with pyc files
    compileall.compile_dir(whl_name)

    # Remove all original py files
    for py_file in glob.glob(whl_name + "/**/*.py"):
        print "Deleting py file: %s" % py_file
        os.remove(py_file)

    for root, dirs, files in os.walk(whl_name):
        for f in files:
            if f.endswith(".py"):
                py_name = os.path.join(root, f)
                print "Removing file: %s" % py_name
                os.remove(py_name)

    # Update the record data
    dist_info = "%s.dist-info" % ("-".join(whl_name.split("-")[:-3]))
    dist_info_path = os.path.join(whl_name, dist_info)
    record_path = os.path.join(dist_info_path, "RECORD")
    rewrite_record(record_path)

    # Update version to include `.compiled`
    update_version(dist_info_path)

    # Rezip the file with the new version info
    rezip_whl(whl_name)

    # Clean up original directory
    shutil.rmtree(whl_name)


def rewrite_record(record_path):
    """Rewrite the record file with pyc files instead of py files."""
    record_data = []
    whl_path = os.path.abspath(os.path.join(record_path, "..", ".."))

    with open(record_path, "r") as record:
        for file_dest, hash, length in csv.reader(record):
            if file_dest.endswith(".py"):
                # Do not keep py files, replace with pyc files
                file_length = 0
                hash = hashlib.new(HASH_TYPE)

                pyc_file = file_dest + "c"
                with open(os.path.join(whl_path, pyc_file), "rb") as f:
                    while True:
                        data = f.read(1024)

                        if not data:
                            break

                        hash.update(data)
                        file_length += len(data)

                hash_value = "%s=%s" % (HASH_TYPE, base64.urlsafe_b64encode(hash.digest()).rstrip('='))
                record_data.append((pyc_file, hash_value, file_length))
            else:
                record_data.append((file_dest, hash, length))

    with open(record_path, "w") as record:
        csv.writer(record, lineterminator='\n').writerows(sorted(set(record_data)))


def update_version(dist_info_path):
    """Update the whl to include .version in the name."""
    with open(os.path.join(dist_info_path, "METADATA"), "r") as f:
        original_metadata = f.read()

    with open(os.path.join(dist_info_path, "METADATA"), "w") as f:
        for line in original_metadata.splitlines():
            if line.startswith("Version: "):
                f.write(line + ".compiled\n")
            else:
                f.write(line + "\n")

    with open(os.path.join(dist_info_path, "metadata.json"), "r") as f:
        json_metadata = json.load(f)

    json_metadata["version"] += ".compiled"

    with open(os.path.join(dist_info_path, "metadata.json"), "w") as f:
        json.dump(json_metadata, f)

    # Rename dist-info directory
    new_dist_info_path = dist_info_path[:-10] + ".compiled.dist-info"
    shutil.move(dist_info_path, new_dist_info_path)


def rezip_whl(whl_name):
    """Rezip the whl file with the new compiled name."""
    new_zip_name = whl_name.split("-")
    new_zip_name[1] += ".compiled"
    new_zip_name = '-'.join(new_zip_name)

    try:
        os.remove(new_zip_name)
    except OSError:
        pass

    shutil.make_archive(new_zip_name, 'zip', whl_name)
    shutil.move(new_zip_name + ".zip", new_zip_name + ".whl")


def main(args=None):
    parser = argparse.ArgumentParser(description='Compile all py files in a wheel')
    parser.add_argument("whl_file", help="Path to whl to convert")
    args = parser.parse_args(args)
    convert_wheel(args.whl_file)


if __name__ == "__main__":
    main()

