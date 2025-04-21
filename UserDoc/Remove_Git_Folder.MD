### To ignore folder and file ###
# Create or edit .gitignore file in the root of your repository
echo "folder_name/" >> .gitignore
echo "file_name" >> .gitignore

# If the folder or file is already tracked, untrack them
git rm -r --cached folder_name
git rm --cached file_name

# Commit the changes
git add .gitignore
git commit -m "Add folder_name and file_name to .gitignore"

# Push to GitHub
git push origin main

### to Remove folder from .gitignore

# Create or edit .gitignore file in the root of your repository
echo ".user_backup/" >> .gitignore

# If the folder is already tracked, untrack it
git rm -r --cached .user_backup

# Commit the changes
git add .gitignore
git commit -m "Exclude .user_backup folder from tracking"

# Push to GitHub
git push origin main