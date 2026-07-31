async def concatenateartists(artistnames: list) -> str:    
    artist_list = artistnames

    if len(artist_list) == 0:
        concatenated_artists = ""
    elif len(artist_list) == 1:
        concatenated_artists = artist_list[0]
    else:
        concatenated_artists = ", ".join(artist_list[:-1]) + f" and {artist_list[-1]}"

    return concatenated_artists