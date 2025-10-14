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
    
    #path = get_movie_url(dbid)
    path = f'videodb://movies/titles/{dbid}'

    #play item
    play_item = xbmcgui.ListItem(path=path,offscreen=True)
    play_item.setProperty('IsPlayable', "true")
    #play_item.setProperty('ForceResolvePlugin', "false")
    
    # add a video info tag, so kodi knows it's a video item
    #play_item_tag = play_item.getVideoInfoTag()
    #play_item_tag.setMediaType('video')
    #play_item_tag.setDbId(int(dbid))
    #play_item_tag.setPath(path)
    #play_item_tag.setFilenameAndPath(path)

    #not finishing properly with setResolvedUrl, using PlayMedia instead, raise an eror in the log but works
    xbmc.executebuiltin(f'PlayMedia("{path}")')

def show_info_dialog(dbid):
    #clear the playlist
    xbmc.PlayList(xbmc.PLAYLIST_VIDEO).clear()

    #close all dialogs
    xbmc.executebuiltin('Dialog.Close(all,true)')
    
    #path = get_movie_url(dbid)
    path = f'videodb://movies/titles/{dbid}'

    #play item
    play_item = xbmcgui.ListItem(path=path,offscreen=True)
    play_item.setProperty('IsPlayable', "true")
    #play_item.setProperty('ForceResolvePlugin', "false")
    
    # add a video info tag, so kodi knows it's a video item
    #play_item_tag = play_item.getVideoInfoTag()
    #play_item_tag.setMediaType('video')
    #play_item_tag.setDbId(int(dbid))
    #play_item_tag.setPath(path)
    #play_item_tag.setFilenameAndPath(path)
    
    dialog = xbmcgui.Dialog()
    dialog.info(play_item)

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
            # Create a URL for a plugin recursive call.
            url = get_url(action='play', id=local_id, title=movie['original_title'])
        #if not ...
        else:
            list_item.setProperty('IsPlayable', 'false')
            if ordered_by == "rank":
                info_tag.setTagLine("Ranked %s\n" % (str(index +1)) + "Not in your libray")
            else:
                info_tag.setTagLine("Not in your libray")
            
            url = get_url(action='play', id="0", title=movie['original_title'])

        # Add the list item to a virtual Kodi folder.
        is_folder = False

        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)

    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(HANDLE)

def get_movie_url(database_id):
    """
    Try to get the movie path
    """

    # Prepare JSON-RPC query to get movie information by database ID
    query = {
        "jsonrpc": "2.0",
        "method": "VideoLibrary.GetMovieDetails",
        "params": {
            "movieid": int(database_id),
            "properties": ["file"]
        },
        "id": 1
    }
    
    # Execute JSON-RPC query
    result = xbmc.executeJSONRPC(json.dumps(query))
    result_dict = json.loads(result)
    
    # Check if the query was successful and extract the URL
    if "result" in result_dict and "moviedetails" in result_dict["result"]:
        movie_details = result_dict["result"]["moviedetails"]
        if "file" in movie_details:
            return movie_details["file"]
    
    return None

def get_list(list_type, list_id):

    list_url = LIST_SERVER_URL + list_type + "?id=" + list_id

    try:
        response = requests.get(list_url, timeout=5)
    except requests.exceptions.RequestException as e:
        print("Error requesting list url")
        raise
    else:
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return None


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
    elif params['action'] == 'play':
        # Play a movie from a provided URL.
        if params['id'] == "0":
            #Propose to search using global search plugin
            choice = xbmcgui.Dialog().yesno('Movie not found', 'Search using global search addon?', defaultbutton=xbmcgui.DLG_YESNO_YES_BTN)
            if choice == True:
                xbmc.executebuiltin("RunScript(script.globalsearch,searchstring=%s)"%(params['title']))
        else:
            play_media(params['id'])
            #show_info_dialog(params['id'])
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
