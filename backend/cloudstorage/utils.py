from .models import File, Folder


def folder_contents(user, folder):
    subfolders = Folder.objects.filter(user=user, parent_folder=folder).order_by('name')
    files = File.objects.filter(owner=user, folder=folder).order_by('name')
    return {
        'current_folder': {'id': folder.id, 'name': folder.name, 'weight': folder.weight},
        'folder_parent_id': folder.parent_folder_id,
        'weight': folder.weight,
        'subfolders': [
            {'id': f.id, 'name': f.name, 'weight': f.weight} for f in subfolders
        ],
        'files': [
            {'id': f.id, 'name': f.name, 'weight': f.weight} for f in files
        ],
    }


def update_parent_weights(folder, delta: int):
    current = folder
    while current is not None:
        current.weight = (current.weight or 0) + delta
        current.save(update_fields=['weight'])
        current = current.parent_folder


def calculate_folder_weight(folder) -> int:
    total = sum(File.objects.filter(folder=folder).values_list('weight', flat=True))
    for sub in Folder.objects.filter(parent_folder=folder):
        total += calculate_folder_weight(sub)
    return total


def gather_descendants(folder):
    """Return (all_subfolders incl. self, all_files) for cascade delete bookkeeping."""
    folders = [folder]
    files = list(File.objects.filter(folder=folder))
    for sub in Folder.objects.filter(parent_folder=folder):
        sub_folders, sub_files = gather_descendants(sub)
        folders.extend(sub_folders)
        files.extend(sub_files)
    return folders, files
