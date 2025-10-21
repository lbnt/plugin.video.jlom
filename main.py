# Copyright (C) 2023, lbnt
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import sys
from urllib.parse import urlencode, parse_qsl
import logging
import json

import xbmc
import xbmcgui
import xbmcplugin
from xbmcaddon import Addon
from xbmcvfs import translatePath

import requests
#import web_pdb;

# Get the plugin url in plugin:// notation.
URL = sys.argv[0]
# Get a plugin handle as an integer number.
HANDLE = int(sys.argv[1])
# Get addon base path
ADDON_PATH = translatePath(Addon().getAddonInfo('path'))
ICONS_DIR = os.path.join(ADDON_PATH, 'resources', 'images', 'icons')
FANART_DIR = os.path.join(ADDON_PATH, 'resources', 'images', 'fanart')

#TMDB url for poster and fanart
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

#lists server url
LIST_SERVER_URL= "http://jlom.fly.dev/"

def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.
    """
    return '{}?{}'.format(URL, urlencode(kwargs))


def list_folders(folder_list):
    """
    Create the list of folders in the Kodi interface.
    """
    if folder_list == None:
        return
    
    #get the folders!
    folders = folder_list['folders']
    

    # Set subtitle
    xbmcplugin.setPluginCategory(HANDLE, folder_list['title'])
    # Set plugin content
    xbmcplugin.setContent(HANDLE, 'movies')
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
    
    # Iterate through folders
    for folder in folders:

        title = folder["title"]

        # Create a list item with a text label.
        list_item = xbmcgui.ListItem(label=title)
        
        # Set additional info for the list item using its InfoTag.
        info_tag = list_item.getVideoInfoTag()
        info_tag.setMediaType('set')
        info_tag.setTitle(title)
        
        # Create a URL for a plugin recursive call.
        if folder["type"] == "folder_list":
            url = get_url(action='list_folders', id=folder["id"])
        elif folder["type"] == "movie_list":
            url = get_url(action='list_movies', id=folder["id"])
        
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
    
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(HANDLE)


def get_media(title, year):
    """
    Try to find the movie in the local database
    """

    #year are often a problem when searching in the library
    #let's be less strict
    year_minus_1 = str(int(year)-1)
    year_plus_1 = str(int(year)+1)
    year_minus_2 = str(int(year)-2)
    year_plus_2 = str(int(year)+2)

    #Construct the JSON-RPC query
    json_query = {
        "jsonrpc": "2.0",
        "method": "VideoLibrary.GetMovies",
        "params": {
            "filter": {
                "and":
                    [
                        {"field": "originaltitle", "operator": "is", "value": title},
                        {"field": "year", "operator": "is", "value": [ year, year_minus_1, year_plus_1, year_minus_2, year_plus_2 ]} ]
            },
            "properties": ["title","imdbnumber"]
        },
        "id": "libMovies"
    }


    # Execute the JSON-RPC query
    response = xbmc.executeJSONRPC(json.dumps(json_query))

    # Parse the response
    result = json.loads(response)

    # Check if any movies were found
    if result["result"]["limits"]["total"] >= 1:
        return result["result"]["movies"][0]["movieid"]
    else:
        return None

def play_media(dbid):

    #clear the playlist
    xbmc.PlayList(xbmc.PLAYLIST_VIDEO).clear()

    #close all dialogs
    xbmc.executebuiltin('Dialog.Close(all,true)')
    
    #use videodb path for direct play
    path = f'videodb://movies/titles/{dbid}'

    #play item
    play_item = xbmcgui.ListItem(path=path,offscreen=True)
    play_item.setProperty('IsPlayable', "true")
    
    xbmcplugin.setResolvedUrl(HANDLE, True, listitem=play_item)

def get_movie_details(id):
    
    #Construct the JSON-RPC query
    json_query = {
        "jsonrpc": "2.0",
        "method": "VideoLibrary.GetMovieDetails",
        "params": {"movieid": id,
        "properties": ["director",
                        "art",
                        "fanart",
                        "file",
                        "genre",
                        "imdbnumber",
                        "lastplayed",
                        "originaltitle",
                        "playcount",
                        "plot",
                        "plotoutline",
                        "premiered",
                        "rating", "runtime", #"resume",
                        "setid", "sorttitle", "streamdetails",
                        "thumbnail",
                        "title",
                        "userrating",
                        "votes"]},
        "id": "1"}

    # Execute the JSON-RPC query
    response = xbmc.executeJSONRPC(json.dumps(json_query))

    # Parse the response
    result = json.loads(response)

    return result


def list_movies(movie_list):
    """
    Create the list of movies in the Kodi interface.
    """

    if movie_list == None:
        return
    
    #get the movies!
    movies = movie_list["movies"]
    ordered_by = movie_list["ordered_by"]

    # Set subtitle
    xbmcplugin.setPluginCategory(HANDLE, movie_list['title'])
    # Set plugin content
    xbmcplugin.setContent(HANDLE, 'movies')

    if ordered_by == "":
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
    elif ordered_by == "rank":
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
    elif ordered_by == "year":
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_VIDEO_YEAR)

    # Iterate through movies.
    for index, movie in enumerate(movies):
        # Create a list item with a text label
        if ordered_by == "rank":
            movie_label = str(index+1) + " - " + movie['title']
        else:
            movie_label = movie['title']

        list_item = xbmcgui.ListItem(label= movie_label)

        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        if movie['poster_path'] != None:
            list_item.setArt({'poster': TMDB_IMAGE_BASE_URL+movie['poster_path']})
        if movie['backdrop_path'] != None:
            list_item.setArt({'fanart': TMDB_IMAGE_BASE_URL+movie['backdrop_path']})
        
        # Set additional info for the list item via InfoTag.
        info_tag = list_item.getVideoInfoTag()
        info_tag.setMediaType('movie')
        info_tag.setTitle(movie['title'])
        #info_tag.setGenres([genre_info['genre']])
        info_tag.setPlot(movie['overview'])
        if movie['release_date'] != '':
            info_tag.setYear(int(movie['release_date'][0:4]))
            #get movie id in library
            local_id = get_media(movie['original_title'],movie['release_date'][0:4])
        else:
            #without year, abort
            local_id = None
        
        #if found, make it playable
        if local_id != None :
            #get the movie details from the db
            movie_details = get_movie_details(local_id)
            
            #set info from db
            info_tag.setDbId(int(local_id))
            info_tag.setPath(f'videodb://movies/titles/{local_id}')
            info_tag.setTitle(movie_details["result"]["moviedetails"]["title"])
            info_tag.setGenres(movie_details["result"]["moviedetails"]["genre"])
            info_tag.setPlot(movie_details["result"]["moviedetails"]["plot"])
            info_tag.setDuration(movie_details["result"]["moviedetails"]["runtime"])
            info_tag.setFilenameAndPath(movie_details["result"]["moviedetails"]["file"])
            info_tag.setPremiered(movie_details["result"]["moviedetails"]["premiered"])
            info_tag.setPlaycount(movie_details["result"]["moviedetails"]["playcount"])

            #difference between available and not available item 
            list_item.setProperty('IsPlayable', 'true')
            #list_item.setInfo("video", {"overlay": xbmcgui.ICON_OVERLAY_HD}) #does not work anyway
            
            
            if ordered_by == "rank":
                info_tag.setTagLine("Ranked %s" % (str(index +1)))
            
            # Direct play url
            url = f'videodb://movies/titles/{local_id}'
        #if not ...
        else:
            list_item.setProperty('IsPlayable', 'false')
            if ordered_by == "rank":
                info_tag.setTagLine("Ranked %s\n" % (str(index +1)) + "Not in your libray")
            else:
                info_tag.setTagLine("Not in your libray")
            # recursive call to offer to search using global search addon
            url = get_url(action='other_action', id=movie['id'], title=movie['original_title'])

        # Add the list item to a virtual Kodi folder.
        is_folder = False

        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)

    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(HANDLE)

def get_list(list_type, list_id):

    list_url = Addon().getSettingString('general_url')
    list_url = list_url if list_url.endswith('/') else list_url + '/'
    list_url += list_type + "?id=" + list_id

    try:
        response = requests.get(list_url, timeout=5)
    except requests.exceptions.RequestException as e:
        xbmc.log("Error requesting list url")
        raise
    else:
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return None

def radarr_add_movie(movie_data):
    """
    Add a movie to Radarr
    """

    # Get Radarr URL and API token from addon settings
    radarr_url = Addon().getSettingString('radarr_url')
    radarr_token = Addon().getSettingString('radarr_token')

    # Build the API endpoint URL
    api_url = radarr_url if radarr_url.endswith('/') else radarr_url + '/'
    api_url += "api/v3/movie"

    # Set request headers with API key
    headers = {
        'X-Api-Key': radarr_token
    }

    try:
        # Send POST request to Radarr to add the movie
        response = requests.post(api_url, headers=headers, json=movie_data, timeout=5)
    except requests.exceptions.RequestException as e:
        # Log error if request fails
        xbmc.log("Error adding movie to Radarr : exception")
        return False
    else:
        # Success: movie added (HTTP 200 or 201)
        if response.status_code in [200, 201]:
            xbmc.log("Movie added to Radarr")
            xbmcgui.Dialog().notification('Radarr', 'Movie added successfully', xbmcgui.NOTIFICATION_INFO)
            return True
        # Bad request (HTTP 400)
        elif response.status_code == 400:
            data = response.json()
            error_message = data[0].get('errorMessage')
            # Movie may already exist
            if error_message == "This movie has already been added":
                xbmc.log("Movie already exists in Radarr")
                xbmcgui.Dialog().notification('Radarr', 'Movie already exists in Radarr', xbmcgui.NOTIFICATION_INFO)
            # Other errors
            else:
                xbmcgui.Dialog().notification('Radarr', 'Failed to add movie to Radarr', xbmcgui.NOTIFICATION_ERROR)
                xbmc.log(f"Failed to add movie to Radarr: {error_message}")
            return False
        else:
            xbmcgui.Dialog().notification('Radarr', 'Failed to add movie to Radarr', xbmcgui.NOTIFICATION_ERROR)
            xbmc.log(f"Failed to add movie to Radarr: {response.status_code} - {response.text}")
            return False

def radarr_add_movie_dialogs(id):
    """
    Add a movie to Radarr with user dialogs for folder and quality selection.
    """

    # Check Radarr connection before proceeding
    if not radarr_check_connection():
        xbmcgui.Dialog().notification('Radarr', 'Connection failed', xbmcgui.NOTIFICATION_ERROR)
        return
    
    # Ask user to select a root folder for the movie
    root_folder_path = radarr_root_folders_dialog()
    if root_folder_path is None:
        xbmcgui.Dialog().notification('Radarr', 'No root folder selected', xbmcgui.NOTIFICATION_ERROR)
        return
    
    # Ask user to select a quality profile for the movie
    quality_profile_id = radar_quality_profiles_dialog()
    if quality_profile_id is None:
        xbmcgui.Dialog().notification('Radarr', 'No quality profile selected', xbmcgui.NOTIFICATION_ERROR)
        return

    # Prepare movie data for Radarr API
    movie_data = {
        'tmdbId': id,  # The TMDB ID of the movie
        'rootFolderPath': root_folder_path,  # Selected root folder path
        'qualityProfileId': str(quality_profile_id),  # Selected quality profile ID
        'monitored': True,  # Monitor the movie for downloads
        'addOptions': {'searchForMovie': True}  # Search for the movie after adding
    }
    
    # Send the request to add the movie to Radarr
    return radarr_add_movie(movie_data)

def radarr_check_connection():
    """
    Check Radarr connection by requesting system status endpoint.
    Returns True if connection is successful, False otherwise.
    """

    # Get Radarr URL and API token from addon settings
    radarr_url = Addon().getSettingString('radarr_url')
    radarr_token = Addon().getSettingString('radarr_token')

    # Build the API endpoint URL for system status
    api_url = radarr_url if radarr_url.endswith('/') else radarr_url + '/'
    api_url += "api/v3/system/status"

    # Set request headers with API key
    headers = {
        'X-Api-Key': radarr_token
    }

    try:
        # Send GET request to Radarr system status endpoint
        response = requests.get(api_url, headers=headers, timeout=5)
    except requests.exceptions.RequestException as e:
        # Log error if request fails
        xbmc.log("Error requesting Radarr status")
        return False
    else:
        # Return True if status code is 200 (OK), otherwise False
        if response.status_code == 200:
            return True
        else:
            return False

def radarr_get_root_folders():
    """
    Get the list of Radarr root folders from the Radarr API.
    Returns a list of root folder objects or None if the request fails.
    """
    # Get Radarr URL and API token from addon settings
    radarr_url = Addon().getSettingString('radarr_url')
    radarr_token = Addon().getSettingString('radarr_token')

    # Build the API endpoint URL for root folders
    api_url = radarr_url if radarr_url.endswith('/') else radarr_url + '/'
    api_url += "api/v3/rootfolder"

    # Set request headers with API key
    headers = {
        'X-Api-Key': radarr_token
    }

    try:
        # Send GET request to Radarr root folders endpoint
        response = requests.get(api_url, headers=headers, timeout=5)
    except requests.exceptions.RequestException as e:
        xbmc.log("Error requesting Radarr root folders")
        raise
    else:
        # Return list of root folders if status code is 200 (OK)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return None

def radarr_root_folders_dialog():
    """
    Show a dialog to select a Radarr root folder.
    Returns the selected folder path or None if cancelled or error.
    """
    # Get root folders from Radarr
    root_folders = radarr_get_root_folders()
    if root_folders is None:
        xbmcgui.Dialog().notification('Radarr', 'Error retrieving root folders', xbmcgui.NOTIFICATION_ERROR)
        return None

    # Extract folder paths for display
    folder_paths = [folder['path'] for folder in root_folders]
    dialog = xbmcgui.Dialog()
    # Show selection dialog
    selected = dialog.select('Select Root Folder', folder_paths)

    # Return selected folder path or None if cancelled
    if selected == -1:
        return None
    else:
        return root_folders[selected]['path']

def radarr_get_quality_profiles():
    """
    Get the list of Radarr quality profiles from the Radarr API.
    Returns a list of quality profile objects or None if the request fails.
    """
    # Get Radarr URL and API token from addon settings
    radarr_url = Addon().getSettingString('radarr_url')
    radarr_token = Addon().getSettingString('radarr_token')

    # Build the API endpoint URL for quality profiles
    api_url = radarr_url if radarr_url.endswith('/') else radarr_url + '/'
    api_url += "api/v3/qualityprofile"

    # Set request headers with API key
    headers = {
        'X-Api-Key': radarr_token
    }

    try:
        # Send GET request to Radarr quality profiles endpoint
        response = requests.get(api_url, headers=headers, timeout=5)
    except requests.exceptions.RequestException as e:
        xbmc.log("Error requesting Radarr quality profiles")
        raise
    else:
        # Return list of quality profiles if status code is 200 (OK)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return None

def radar_quality_profiles_dialog():
    """
    Show a dialog to select a Radarr quality profile.
    Returns the selected profile ID or None if cancelled or error.
    """
    # Get quality profiles from Radarr
    profiles = radarr_get_quality_profiles()
    if profiles is None:
        xbmcgui.Dialog().notification('Radarr', 'Error retrieving quality profiles', xbmcgui.NOTIFICATION_ERROR)
        return None

    # Extract profile names for display
    profile_names = [profile['name'] for profile in profiles]
    dialog = xbmcgui.Dialog()
    # Show selection dialog
    selected = dialog.select('Select Quality Profile', profile_names)

    # Return selected profile ID or None if cancelled
    if selected == -1:
        return None
    else:
        return profiles[selected]['id']

def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring
    """

    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if not params:
        # If the plugin is called from Kodi UI without any parameters,
        # display the master list
        list_folders(get_list("folder_list", "master"))
    elif params['action'] == 'list_movies':
        # display a list of movies        
        list_movies(get_list("movie_list", params['id']))
    elif params['action'] == 'list_folders':
        # display a list of folders        
        list_folders(get_list("folder_list", params['id']))
    elif params['action'] == 'other_action':
        # last stage callback

        # the movie was not found in the library and we propose other actions
        other_actions = ['Search in library']
        if Addon().getSettingBool('radarr_enable') == True :
            other_actions.append('Add to radarr')
        
        choice = xbmcgui.Dialog().contextmenu(other_actions)
        if choice == 0:
            #search in library
            xbmc.executebuiltin("RunScript(script.globalsearch,movies=true&searchstring=%s)"%(params['title']))
        elif choice == 1:
            #add to Radarr
            radarr_add_movie_dialogs(params['id'])
    else:
        # If the provided paramstring does not contain a supported action
        # we raise an exception. This helps to catch coding errors,
        # e.g. typos in action names.
        raise ValueError(f'Invalid paramstring: {paramstring}!')

if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    #logging.basicConfig(level=logging.DEBUG)

    #web_pdb.set_trace()

    router(sys.argv[2][1:])
