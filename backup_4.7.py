import os
import sys
import logging
import shutil
from datetime import datetime
from pathlib import Path
import zipfile
from tqdm import tqdm
import hashlib

FEEDBACK_FILE_PATH = Path("C:/Storage/SpeedTools/Python/FeedBack/App/Backup/Backup_App/FeedBack.txt")

backup_dir = Path('.user_backup')
backup_dir.mkdir(exist_ok=True)

logging.basicConfig(
    filename=backup_dir / 'backup_restore.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

ignored_items = set()
ignore_log_path = backup_dir / 'ignored_items.log'
ignored_sizes = set()

if ignore_log_path.exists():
    with open(ignore_log_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.endswith('MB') or line.endswith('GB'):
                ignored_sizes.add(line)
            else:
                ignored_items.add(line)

def format_table(headers, rows, widths=None):
    if not widths:
        widths = [max(len(str(row[i])) for row in [headers] + rows) + 2 for i in range(len(headers))]
    
    h_line = '+' + '+'.join('-' * w for w in widths) + '+'
    header_str = '|' + '|'.join(f"{str(h):^{w}}" for h, w in zip(headers, widths)) + '|'
    row_lines = []
    for row in rows:
        row_lines.append(h_line)
        row_lines.append('|' + '|'.join(f"{str(cell):^{w}}" for cell, w in zip(row, widths)) + '|')
    return '\n'.join([h_line, header_str] + row_lines + [h_line])

def save_ignored_items():
    with open(ignore_log_path, 'w') as f:
        for item in sorted(ignored_items | ignored_sizes):
            f.write(f"{item}\n")

def get_next_backup_number():
    backup_dir = Path('.user_backup')
    existing_backups = list(backup_dir.glob('[0-9][0-9]__*.zip'))
    if not existing_backups:
        return "01"
    numbers = [int(b.name[:2]) for b in existing_backups]
    next_num = max(numbers) + 1
    return f"{next_num:02d}"

def calculate_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_file_size_mb(file_path):
    return os.path.getsize(file_path) / (1024 * 1024)

def parse_size_limit(size_str):
    size_str = size_str.upper().strip()
    if size_str.endswith('KB'):
        return float(size_str[:-2]) / 1024 # Convert KB to MB
    elif size_str.endswith('MB'):
        return float(size_str[:-2])
    elif size_str.endswith('GB'):
        return float(size_str[:-2]) * 1024
    # Add TB support
    elif size_str.endswith('TB'):
        return float(size_str[:-2]) * 1024 * 1024
    try:
        # Assume MB if no unit is specified (or handle as error)
        return float(size_str)
    except ValueError:
        # Handle cases where conversion to float fails
        raise ValueError(f"Invalid size format: {size_str}")

def should_ignore_size(file_path):
    file_size_mb = get_file_size_mb(file_path)
    for size_limit in ignored_sizes:
        limit_mb = parse_size_limit(size_limit)
        if file_size_mb >= limit_mb:
            return True
    return False

def create_backup(comment=''):
    temp_dir = None
    backup_path = None # Initialize backup_path
    try:
        backup_dir = Path('.user_backup')
        backup_dir.mkdir(exist_ok=True)

        next_num = get_next_backup_number()
        formatted_comment = comment.replace(' ', '_') if comment else 'backup'
        backup_name = f"{next_num}__{formatted_comment}.zip"
        backup_path = backup_dir / backup_name

        total_files = 0
        files_to_backup = []
        original_hashes = {}
        ignore_paths = {Path(item).resolve() if not item.startswith('/') else Path(item[1:]).resolve() for item in ignored_items}
        script_name = os.path.basename(__file__)

        for item in os.listdir('.'):
            # Ignore hidden files/folders, the backup dir, the script itself, and the log file
            if item.startswith('.') or item == backup_dir.name or item == script_name or item == 'backup_restore.log':
                continue

            item_path = Path(item).resolve()
            # Check against user-defined ignore list
            should_ignore_user = (item_path in ignore_paths or
                                  any(item_path.is_relative_to(ignore_path) for ignore_path in ignore_paths))

            if not should_ignore_user:
                if item_path.is_file():
                    # Check size limit for files
                    if not should_ignore_size(item_path):
                        total_files += 1
                        files_to_backup.append(item_path)
                        original_hashes[str(item_path)] = calculate_file_hash(item_path)
                elif item_path.is_dir(): # Only process directories explicitly
                    for file_path in item_path.rglob('*'):
                        # Ignore hidden files/folders within subdirectories
                        if any(part.startswith('.') for part in file_path.parts):
                            continue

                        if file_path.is_file():
                            file_resolved = file_path.resolve()
                            # Check against user-defined ignore list and size limit
                            should_ignore_file = (file_resolved in ignore_paths or
                                                any(file_resolved.is_relative_to(ignore_path) for ignore_path in ignore_paths) or
                                                should_ignore_size(file_resolved))
                            if not should_ignore_file:
                                total_files += 1
                                files_to_backup.append(file_path)
                                original_hashes[str(file_path)] = calculate_file_hash(file_path)

        if total_files == 0:
            print("No files to backup after applying ignore list!")
            return False

        print("\nCreating backup archive...")
        with zipfile.ZipFile(backup_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            with tqdm(total=total_files, desc="Creating backup", unit="files") as pbar:
                for file_path in files_to_backup:
                    # Normalize the path to use forward slashes
                    arcname = str(file_path.relative_to(Path.cwd())).replace('\\', '/')
                    archive.write(file_path, arcname)
                    pbar.update(1)

        print("\nVerifying backup integrity...")
        temp_dir = Path('temp_verify')
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir()

        verified_count = 0
        with zipfile.ZipFile(backup_path, 'r') as archive:
            print("Testing ZIP archive integrity...")
            try:
                test_result = archive.testzip()
                if test_result is not None:
                     raise Exception(f"ZIP file is corrupted: First bad file is {test_result}")
            except Exception as e:
                raise Exception(f"ZIP file integrity check failed: {str(e)}")

            print("Verifying individual files...")
            with tqdm(total=total_files, desc="Verifying files", unit="files") as pbar:
                for file_path in files_to_backup:
                    # Normalize the path to match what was written to the archive
                    zip_path = str(file_path.relative_to(Path.cwd())).replace('\\', '/')
                    try:
                        archive.extract(zip_path, temp_dir)
                        temp_file_path = temp_dir / zip_path
                        if not temp_file_path.exists():
                             raise Exception(f"Extracted file not found: {temp_file_path}")
                        if calculate_file_hash(temp_file_path) == original_hashes[str(file_path)]:
                            verified_count += 1
                        else:
                            raise Exception(f"File verification failed (hash mismatch): {file_path}")
                        pbar.update(1)
                    except KeyError as e: # Handle case where file is in archive but not expected
                        raise Exception(f"Verification failed: Unexpected file in archive {e}")
                    except Exception as e:
                        raise Exception(f"Verification failed for {file_path}: {str(e)}")

        if verified_count != total_files:
            raise Exception(f"Only {verified_count}/{total_files} files verified successfully")

        print(f"\nBackup verification completed successfully! ({verified_count}/{total_files} files verified)")

        size_mb = round(os.path.getsize(backup_path) / (1024 * 1024), 2)
        log_msg = f"{backup_name} - {size_mb} MB (Verified {verified_count} files)"
        logging.info(log_msg)
        print(f"Backup created and verified: {backup_name}")
        return True

    except Exception as e:
        logging.error(f"Backup failed: {str(e)}")
        print(f"Error creating backup: {str(e)}")
        # Check if backup_path was assigned before trying to unlink
        if backup_path and backup_path.exists():
            try:
                backup_path.unlink()
                print("Incomplete or failed backup file was removed.")
            except Exception as del_e:
                print(f"Warning: Could not remove incomplete backup file {backup_path}. Error: {del_e}")
        return False
    finally:
        if temp_dir and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as clean_e:
                print(f"Warning: Could not remove temporary verification directory {temp_dir}. Error: {clean_e}")

def create_backup_with_ignore(comment=''):
    return create_backup(comment)

def handle_ignore_operations():
    while True:
        print("\n=== Ignore Operations ===")
        print("1. Add File")
        print("2. Add Folder")
        print("3. Ignore File Size")
        print("4. View User Ignored Items")
        print("5. View Built-in Ignored Items")
        print("6. Remove Ignored Item")
        print("0. Return to Main Menu")

        choice = input("\nEnter your choice (0-6): ")

        if choice == '1':
            file_name = input("Enter file name (e.g., 'core.py' or 'data.txt'): ").strip()
            if file_name:
                if not (file_name.upper().endswith(('KB', 'MB', 'GB', 'TB')) and file_name[:-2].replace('.', '', 1).isdigit()) and not file_name.startswith(('/', '\\')): # Added KB/TB check
                    file_name = file_name.replace('\\', '/')
                    ignored_items.add(file_name)
                    save_ignored_items()
                    print(f"File '{file_name}' added to ignore list")
                else:
                    print("Invalid file name format (cannot start with '/' or '\\', or look like a size limit).")

        elif choice == '2':
            print("Instructions: Enter folder path (e.g., 'core', 'my_data/sub' or 'my_data\\sub'). It will be stored internally starting with '/'.")
            folder_name = input("Enter folder path: ").strip()
            if folder_name:
                if not (folder_name.upper().endswith(('KB', 'MB', 'GB', 'TB')) and folder_name[:-2].replace('.', '', 1).isdigit()): # Added KB/TB check
                    normalized_folder_name = folder_name.replace('\\', '/')
                    if normalized_folder_name.startswith('/'):
                        normalized_folder_name = normalized_folder_name[1:]
                    stored_folder_name = '/' + normalized_folder_name
                    ignored_items.add(stored_folder_name)
                    save_ignored_items()
                    print(f"Folder '{stored_folder_name}' added to ignore list")
                else:
                     print("Invalid folder name format (looks like a size limit).")

        elif choice == '3':
            # Updated prompt to include KB and TB
            size_limit = input("Enter size limit (e.g., '500KB', '50MB', '1GB', '0.5TB'): ").strip()
            size_limit_upper = size_limit.upper()
            # Updated validation to include KB and TB
            if size_limit_upper.endswith(('KB', 'MB', 'GB', 'TB')):
                 try:
                     # Use the parse_size_limit function indirectly for validation
                     parse_size_limit(size_limit)
                     ignored_sizes.add(size_limit_upper) # Store the original input format (uppercase)
                     save_ignored_items()
                     print(f"Size limit '{size_limit_upper}' added to ignore list")
                 except ValueError:
                      print("Invalid numeric value for size limit.")
            else:
                # Updated error message
                print("Invalid format! Use e.g., '500KB', '50MB', '1GB', '0.5TB'")

        elif choice == '4':
            if not (ignored_items or ignored_sizes):
                print("No files, folders, or sizes currently ignored by user!")
            else:
                print("\nUser Ignored Files, Folders, and Sizes:")
                ignore_list_data = []
                all_ignored_strings = sorted(list(ignored_items | ignored_sizes))

                for i, item_str in enumerate(all_ignored_strings):
                    item_type = "Unknown"
                    if item_str in ignored_sizes:
                        item_type = "Size"
                    elif item_str.startswith('/'):
                        item_type = "Folder"
                    else:
                        item_type = "File"
                    ignore_list_data.append([i + 1, "ignored", item_str, item_type])

                print(format_table(
                    ['#', 'Status', 'Item', 'Type'],
                    ignore_list_data
                ))

        elif choice == '5':
            print("\nBuilt-in Ignored Items (Always Ignored):")
            print(f"- Backup directory: {backup_dir.name}")
            print(f"- This script: {os.path.basename(__file__)}")
            print("- Log file: backup_restore.log")
            print("- All files/folders starting with '.'")

        elif choice == '6':
            if not (ignored_items or ignored_sizes):
                print("Ignore list is already empty!")
                continue

            print("\nSelect item to remove from ignore list:")
            ignore_list_data = []
            all_ignored_strings = sorted(list(ignored_items | ignored_sizes))

            for i, item_str in enumerate(all_ignored_strings):
                item_type = "Size" if item_str in ignored_sizes else ("Folder" if item_str.startswith('/') else "File")
                ignore_list_data.append([i + 1, item_str, item_type])

            print(format_table(
                ['#', 'Item', 'Type'],
                ignore_list_data
            ))

            try:
                idx_to_remove = int(input("Enter the number of the item to remove (or 0 to cancel): ")) - 1
                if idx_to_remove == -1:
                    continue
                if 0 <= idx_to_remove < len(all_ignored_strings):
                    item_to_remove = all_ignored_strings[idx_to_remove]
                    removed = False
                    if item_to_remove in ignored_items:
                        ignored_items.remove(item_to_remove)
                        removed = True
                    elif item_to_remove in ignored_sizes:
                        ignored_sizes.remove(item_to_remove)
                        removed = True

                    if removed:
                        save_ignored_items()
                        print(f"Item '{item_to_remove}' removed from the ignore list.")
                    else:
                        print(f"Error: Could not find '{item_to_remove}' in internal lists.")
                else:
                    print("Invalid selection! Number out of range.")
            except ValueError:
                print("Invalid input! Please enter a number.")

        elif choice == '0':
            break

        else:
            print("Invalid choice! Please enter a number between 0 and 6.")

def restore_backup(backup_file):
    try:
        backup_path = Path('.user_backup') / backup_file
        
        ignore_paths = {Path(item).resolve() if not item.startswith('/') else Path(item[1:]).resolve() for item in ignored_items}

        items_to_check = []
        for item in os.listdir('.'):
            item_path = Path(item).resolve()
            if item not in ['.user_backup', os.path.basename(__file__), 'backup_restore.log']:
                should_ignore = (item_path in ignore_paths or 
                               any(item_path.is_relative_to(ignore_path) for ignore_path in ignore_paths))
                if not should_ignore:
                    items_to_check.append(item)

        if not items_to_check:
            print("No files or folders to delete in the current directory (after applying ignore list).")
            items_to_delete = []
        else:
            print("\nThe following files and folders are in the current directory (ignore list applied):")
            for idx, item in enumerate(items_to_check, 1):
                item_path = Path(item)
                item_type = "Folder" if item_path.is_dir() else "File"
                print(f"{idx}. {item} ({item_type})")
            
            print("\nEnter the numbers of the items you want to KEEP (e.g., '1 3 5'), or press Enter to delete all listed:")
            keep_input = input("Your choice: ").strip()
            
            if keep_input:
                try:
                    keep_indices = [int(i) - 1 for i in keep_input.split()]
                    if any(i < 0 or i >= len(items_to_check) for i in keep_indices):
                        print("Invalid selection! One or more numbers are out of range. Aborting restore.")
                        return False
                    items_to_keep = [items_to_check[i] for i in keep_indices]
                    items_to_delete = [item for item in items_to_check if item not in items_to_keep]
                except ValueError:
                    print("Invalid input! Please enter numbers separated by spaces. Aborting restore.")
                    return False
            else:
                items_to_delete = items_to_check

        if items_to_delete:
            print("\nCleaning unselected items from current directory...")
            for item in items_to_delete:
                try:
                    if os.path.isfile(item):
                        os.remove(item)
                    else:
                        shutil.rmtree(item)
                    print(f"Deleted: {item}")
                except PermissionError:
                    print(f"Unable to delete {item}. Please close any programs using it and press Enter to continue...")
                    input()
                    os.remove(item) if os.path.isfile(item) else shutil.rmtree(item)
                    print(f"Deleted: {item}")
            print("Unselected items cleaned.")
        else:
            print("\nAll listed items selected to keep. Proceeding with restore...")

        with zipfile.ZipFile(backup_path, 'r') as archive:
            total_files = len(archive.namelist())
            with tqdm(total=total_files, desc="Restoring backup", unit="files") as pbar:
                for file in archive.namelist():
                    archive.extract(file)
                    pbar.update(1)

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        deleted_items_str = ", ".join(items_to_delete) if items_to_delete else "None"
        log_msg = f"{backup_file} - Restored (Deleted items: {deleted_items_str})"
        logging.info(log_msg)
        print("\nRestore completed successfully!")
        return True

    except Exception as e:
        logging.error(f"Restore failed: {str(e)}")
        print(f"Error during restore: {str(e)}")
        return False
    
def list_backups():
    backup_dir = Path('.user_backup')
    if not backup_dir.exists():
        return []
    
    backups = []
    for f in backup_dir.glob('*.zip'):
        size_mb = round(f.stat().st_size / (1024 * 1024), 2)
        created = datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
        comment = f.stem.split('__', 1)[1] if '__' in f.stem else ''
        backups.append([f.name, created, comment, f"{size_mb} MB"])
    
    sorted_backups = sorted(backups, key=lambda x: x[1])  # Sort oldest to newest
    numbered_backups = [[i + 1] + backup for i, backup in enumerate(sorted_backups)]  # Number from 1 (oldest) to n (newest)
    return numbered_backups

def regenerate_log():
    try:
        log_path = Path('.user_backup') / 'backup_restore.log'
        backups = list_backups()
        
        if not backups:
            print("No backups found to regenerate log!")
            return False

        with open(log_path, 'w') as f:
            f.write("Available Backups:\n")
            f.write(format_table(
                ['#', 'Backup Name', 'Created', 'Comment', 'Size'],
                [[i+1] + backup for i, backup in enumerate(backups)]
            ))
        print("Log file has been regenerated successfully!")
        return True
    except Exception as e:
        print(f"Error regenerating log: {str(e)}")
        return False

def handle_log_operations():
    while True:
        print("\n=== Log Operations ===")
        print("1. View Log")
        print("2. Regenerate Log")
        print("3. Back to Main Menu")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == '1':
            log_path = Path('.user_backup') / 'backup_restore.log'
            if log_path.exists():
                with open(log_path, 'r') as f:
                    print("\n=== Backup Log History ===")
                    print(f.read())
            else:
                print("No log file found!")

        elif choice == '2':
            confirm = input("This will clear the existing log and create a new one. Continue? (y/n): ")
            if confirm.lower() == 'y':
                regenerate_log()

        elif choice == '3':
            break
        else:
            print("Invalid choice! Please enter a number between 1 and 3.")

def delete_backup(backup_file):
    try:
        backup_path = Path('.user_backup') / backup_file
        if backup_path.exists():
            os.remove(backup_path)
            log_msg = f"{backup_file} - Deleted"
            logging.info(log_msg)
            print(f"Backup {backup_file} was successfully deleted!")
            return True
        return False
    except Exception as e:
        logging.error(f"Delete failed: {str(e)}")
        print(f"Error deleting backup: {str(e)}")
        return False

def rename_backup(backup_path: Path, new_prefix: str):
    """Renames a backup file, adding, replacing, or removing a prefix like [BAD-ERROR] or [Custom]."""
    try:
        if not backup_path.exists():
            print("Backup file not found!")
            return False

        old_name = backup_path.name
        parts = old_name.split('__', 1)
        number = parts[0]
        rest_of_name = parts[1] if len(parts) > 1 else ''

        # Remove existing prefix if present
        comment_part = rest_of_name # Start assuming the whole rest is the comment
        if rest_of_name.startswith('[') and ']_' in rest_of_name:
            prefix_end_index = rest_of_name.find(']_') + 2
            comment_part = rest_of_name[prefix_end_index:] # Get the part after the prefix

        # Ensure the comment part ends with .zip if the original name did
        # Handle cases: NN__comment.zip, NN__[TAG]_comment.zip, NN__.zip, NN__[TAG]_.zip
        if not comment_part.endswith('.zip') and rest_of_name.endswith('.zip'):
             comment_part += '.zip'
        elif comment_part == '' and rest_of_name.endswith('.zip'): # Case NN__[TAG]_.zip
             comment_part = '.zip'


        # Construct new name based on whether a prefix is provided
        if new_prefix:
            # Ensure the provided prefix is enclosed in brackets if it's not empty
            formatted_prefix = f"[{new_prefix.strip('[]')}]" # Clean up just in case user adds brackets
            new_name = f"{number}__{formatted_prefix}_{comment_part}"
        else:
            # No prefix means removing the mark
            new_name = f"{number}__{comment_part}"


        # Avoid renaming if the name is already correct (e.g., removing mark from unmarked file)
        if old_name == new_name:
            print(f"Backup '{old_name}' already has the desired format. No change needed.")
            return True

        new_path = backup_path.parent / new_name

        backup_path.rename(new_path)
        log_msg = f"Renamed backup: {old_name} -> {new_name}"
        logging.info(log_msg)
        print(f"Backup renamed to: {new_name}")
        return True

    except Exception as e:
        logging.error(f"Rename failed for {backup_path.name}: {str(e)}")
        print(f"Error renaming backup: {str(e)}")
        return False
    
def handle_mark_backup():
    """Handles marking backups as Good, Bad, Custom, or removing marks."""
    while True:
        print("\n=== Mark Backup ===")
        print("1. Mark as Good ([Good-Version])")
        print("2. Mark as Bad ([BAD-ERROR])")
        print("3. Add Custom Mark ([Your-Mark])")
        print("4. Remove Mark")
        print("0. Back to Main Menu")

        choice = input("Enter your choice (0-4): ") # Updated range

        prefix = None
        action_verb = ""

        if choice == '1':
            prefix = "Good-Version"
            action_verb = "Good"
        elif choice == '2':
            prefix = "BAD-ERROR"
            action_verb = "Bad"
        elif choice == '3':
            custom_mark = input("Enter custom mark text (e.g., Needs-Review, Archived): ").strip()
            if not custom_mark:
                print("Custom mark cannot be empty. Operation cancelled.")
                continue # Go back to mark menu
            # Basic validation: avoid characters problematic in filenames if needed, but keep simple for now
            prefix = custom_mark
            action_verb = f"Custom ({prefix})"
        elif choice == '4':
            prefix = "" # Empty string signifies removal
            action_verb = "Remove Mark from"
        elif choice == '0':
            break # Exit the mark menu, return to main menu
        else:
            print("Invalid choice! Please enter a number between 0 and 4.")
            continue # Go back to mark menu

        # Proceed only if a valid action (1-4) was chosen
        if action_verb:
            backups = list_backups()
            if not backups:
                print("No backups found!")
                continue # Go back to the mark menu

            print(f"\nAvailable Backups (Select one to {action_verb}):")
            print(format_table(
                ['#', 'Backup Name', 'Created', 'Comment', 'Size'],
                 [[row[0], row[1], row[2], row[3], row[4]] for row in backups]
            ))

            try:
                idx = int(input(f"\nSelect backup number (or 0 to cancel): ")) - 1
                if idx == -1: # User chose 0 to cancel
                     continue # Go back to the mark menu
                if 0 <= idx < len(backups):
                    selected_backup_name = backups[idx][1] # Get the filename from the list
                    backup_path = Path('.user_backup') / selected_backup_name
                    rename_backup(backup_path, prefix) # Pass the determined prefix (or "" for removal)
                else:
                    print("Invalid selection! Number out of range.")
            except ValueError:
                print("Invalid selection! Please enter a valid number.")
            # Loop continues in the mark menu after attempting an action or error

def handle_feedback():
    """Handles collecting and storing user feedback."""
    print("\n=== Submit Feedback ===")
    print("Enter your feedback below. Type 'EOF' on a new line when finished.")

    feedback_lines = []
    while True:
        try:
            line = input("> ")
            if line.strip().upper() == 'EOF':
                break
            feedback_lines.append(line)
        except EOFError: # Handle Ctrl+D or similar EOF signals
            break

    if not feedback_lines:
        print("No feedback entered.")
        return

    feedback_text = "\n".join(feedback_lines).strip()

    if not feedback_text:
        print("No feedback entered.")
        return

    try:
        # Ensure the directory exists
        FEEDBACK_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Append feedback to the file
        with open(FEEDBACK_FILE_PATH, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"--- Feedback Received: {timestamp} ---\n")
            f.write(feedback_text)
            f.write("\n---------------------------------------\n\n")

        print("\nThank you for your feedback! It has been saved.")
        logging.info("User feedback submitted.")

    except Exception as e:
        error_msg = f"Failed to save feedback: {str(e)}"
        print(f"\nError: {error_msg}")
        logging.error(error_msg)

def main():
    while True:
        print("\n=== Backup/Restore Application ===")
        print("1. Create Backup")
        print("2. Create Ignore List")
        print("3. Restore Backup")
        print("4. Log Operations")
        print("5. Delete Backup")
        print("6. Mark Backup")
        print("9. Submit Feedback") # Added option 9
        print("0. Exit")

        choice = input("\nEnter your choice (0-6, 9): ") # Updated choices display

        if choice == '1':
            comment = input("Enter a comment for the backup (or press Enter to skip): ").strip()
            create_backup(comment)

        elif choice == '2':
            handle_ignore_operations()

        elif choice == '3':
            backups = list_backups()
            if not backups:
                print("No backups found!")
                continue

            print("\nAvailable Backups:")
            print(format_table(
                ['#', 'Backup Name', 'Created', 'Size'],
                [[row[0], row[1], row[2], row[4]] for row in backups]
            ))

            try:
                idx = int(input("\nSelect backup number to restore: ")) - 1
                if 0 <= idx < len(backups):
                    selected_backup_name = backups[idx][1]
                    if "[BAD-ERROR]" in selected_backup_name:
                         confirm_bad = input(f"Warning: Backup '{selected_backup_name}' is marked as BAD. Are you sure you want to restore it? (y/n): ")
                         if confirm_bad.lower() != 'y':
                             print("Restore cancelled.")
                             continue

                    careful = input("Are you sure you want to delete applicable files/folders in the current directory and restore? (y/n): ")
                    if careful.lower() == 'y':
                        restore_backup(selected_backup_name)
                else:
                    print("Invalid selection! Number out of range.")
            except ValueError:
                print("Invalid selection! Please enter a valid number.")

        elif choice == '4':
            handle_log_operations()

        elif choice == '5':
            backups = list_backups()
            if not backups:
                print("No backups found!")
                continue
            print("\nAvailable Backups:")
            print(format_table(
                ['#', 'Backup Name', 'Created', 'Comment', 'Size'],
                [[row[0], row[1], row[2], row[3], row[4]] for row in backups]
            ))
            try:
                idx = int(input("\nSelect backup number to delete: ")) - 1
                if 0 <= idx < len(backups):
                    confirm = input(f"Are you sure you want to delete backup '{backups[idx][1]}'? (y/n): ")
                    if confirm.lower() == 'y':
                        delete_backup(backups[idx][1])
                else:
                    print("Invalid selection! Number out of range.")
            except ValueError:
                print("Invalid selection!")

        elif choice == '6':
            handle_mark_backup()

        elif choice == '9': # Added case for feedback
            handle_feedback()

        elif choice == '0':
            print("Goodbye!")
            break

        else:
            # Updated invalid choice message
            print("Invalid choice! Please enter a number between 0-6 or 9.")

if __name__ == "__main__":
    main()