def reformat_filename(name: str) -> str:
    return name.strip().replace(" ", "-")

def generate_logo_key(filename: str, project_id: int) -> str:
    return f"project-{project_id}-logo-{filename}"

def get_logo_name_for_user(key: str, project_id: int) -> str:
    return key[len(f"project-{project_id}-logo-"):]