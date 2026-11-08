def format_artist_details(recording):
    # Create artist dictionaries
    artist_list = []
    for artist in recording['artist_data']:
        # Find any legal names
        legal_names = [
            alias['alias']
            for alias in artist.get("alias-list", [])
            if alias.get("type") == "Legal name"
        ]

        # Add to list of artists
        artist_list.append({
            'artist_name': artist["name"],
            'legal_name': legal_names,
            'gender': artist.get("gender", ""),
            'date_of_birth': artist.get("life-span", {}).get('begin'), 
            'country': artist.get("country", ""),
            'area': artist.get("begin-area", {}).get('name'),
        })

    return artist_list

def add_artist_rels(recording, formatted_recording):
    artist_relations = recording.get("artist-relation-list", [])
    for rel in artist_relations:
        rel_type = rel.get("type")
        rel_artist_name = rel.get("artist", {}).get("name")
        if rel_type and rel_artist_name:
            if rel_type in formatted_recording:
                formatted_recording[rel_type].append(rel_artist_name)
            else:
                formatted_recording[rel_type] = [rel_artist_name]
    return formatted_recording

def add_work_rels(recording, formatted_recording):
    work_data = recording.get('work_data')
    artist_relations = work_data.get("artist-relation-list", [])
    for rel in artist_relations:
        rel_type = rel.get("type")
        rel_artist_name = rel.get("artist", {}).get("name")
        if rel_type and rel_artist_name:
            if rel_type in formatted_recording:
                formatted_recording[rel_type].append(rel_artist_name)
            else:
                formatted_recording[rel_type] = [rel_artist_name]
    return formatted_recording

def add_label(recording, formatted_recording):
    label_relations = recording.get("label_data", [])
    for rel in label_relations:
        label_name = rel.get("label", {}).get("name")
        if label_name:
            if 'label' in formatted_recording:
                formatted_recording['label'].append(label_name)
            else:
                formatted_recording['label'] = [label_name]
    return formatted_recording

def format_recording(recording):
    # Create dictionary and add title
    formatted_recording = {}
    formatted_recording['track'] = recording.get('title', '')  

    # Add related people
    formatted_recording = add_artist_rels(recording, formatted_recording)

    #Add people from works
    formatted_recording = add_work_rels(recording, formatted_recording)

    #Add label from works
    formatted_recording = add_label(recording, formatted_recording)

    # Add tags (genres)
    tag_list = recording.get('tag-list', [])
    formatted_recording['tags'] = [tag['name'] for tag in tag_list] if tag_list else []

    # Add artist dictionaries
    formatted_recording['artist'] = format_artist_details(recording)

    return formatted_recording