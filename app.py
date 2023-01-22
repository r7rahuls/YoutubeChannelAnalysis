# importing required libraries
import streamlit as st
import requests
from streamlit_lottie import st_lottie
import pandas as pd
from googleapiclient.discovery import build
import numpy as np


 # intial api setup
api_key = st.secrets["api_key"] # obtain your own api key and replace this line with -> api_key = "YOUR_API_KEY"
api_service_name = "youtube"
api_version = "v3"

# Create an API client
youtube =build(api_service_name, api_version, developerKey=api_key)



# configure the streamlit webapp page in wide layout mode
st.set_page_config(page_title="Youtube Channel Analyzer", layout="wide")


# --- request function that is used to load the animation url ---
def load_url(url):
    r = requests.get(url)       # to access the animation link
    if r.status_code !=200:
        return None
    return r.json()

# Animation Assests
utubeIcon = load_url("https://assets8.lottiefiles.com/packages/lf20_A6VCTi95cd.json")



# --- Required functions ---


# function to get channel statistics such as subscriber count, total views, total videos etc.
def get_channel_statistics(youtube, channel_id):
    # create request to the YouTube API to retrieve channel information
    request = youtube.channels().list(part = 'snippet, contentDetails, statistics', 
                                     id = channel_id)
    # execute the request
    response = request.execute()
    
    # extract various pieces of information about the channel
    channelName = response['items'][0]['snippet']['title']
    subscriberCount = response['items'][0]['statistics']['subscriberCount']
    CviewCount =  response['items'][0]['statistics']['viewCount']
    videoCount =  response['items'][0]['statistics']['videoCount']
    playlistId = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    channelImg = response['items'][0]['snippet']['thumbnails']['medium']['url']
    
    # return all the extracted information in the form of a tuple
    return channelName, videoCount, subscriberCount, CviewCount, playlistId, channelImg



# function to get id of all the videos available in a playlist
def get_video_ids(youtube, playlistId):
    # create request to the YouTube API to retrieve video IDs from a specific playlist
    request = youtube.playlistItems().list(part = 'contentDetails', playlistId = playlistId, maxResults = 50)
    # execute the request
    response = request.execute()
    
    # create an empty list to store the video IDs
    videoIds = []
    # loop through the items in the response and extract the video IDs
    for i in range(len(response['items'])):
        videoIds.append(response['items'][i]['contentDetails']['videoId'])
    
    # check if there are more pages of results
    nextPageToken = response.get('nextPageToken')
    morePages = True
    while morePages:
        # if there are no more pages, set morePages to False
        if nextPageToken is None:
            morePages = False
        else:
            # create a new request for the next page of results
            request = youtube.playlistItems().list(part = 'contentDetails',
                                                  playlistId = playlistId,
                                                  maxResults = 50,
                                                  pageToken = nextPageToken)
            # execute the request
            response = request.execute()
            # loop through the items in the response and extract the video IDs
            for i in range(len(response['items'])):
                videoIds.append(response['items'][i]['contentDetails']['videoId'])
                
            # update the nextPageToken variable for the next iteration
            nextPageToken = response.get('nextPageToken')
            
    # return the list of video IDs
    return videoIds


# Function to get video details
def get_video_details(youtube, videoIds):
    # Initialize an empty list to store the video statistics
    videoStatsList = []
    # Loop through the video IDs in chunks of 50
    for i in range(0, len(videoIds), 50):
        # Create a request to the YouTube API to retrieve statistics for the current chunk of video IDs
        request = youtube.videos().list(part = 'snippet, statistics',
                                       id = ','.join(videoIds[i:i+50]))
        # Execute the request
        response = request.execute()
        
        # Loop through the videos in the response
        for video in response['items']:
            # Need to handle the hidden like count or comment turned off exception
            try:
                # Create a dictionary to store the video statistics
                videoStats = dict(title = video['snippet']['title'],
                         publishedAt = video['snippet']['publishedAt'],
                         viewCount = video['statistics']['viewCount'],
                         likeCount = video['statistics']['likeCount'],
                         commentCount = video['statistics']['commentCount']
                         )
                
            except KeyError:
                # If like count or comment count are turned off then exception occur
                videoStats = dict(title = video['snippet']['title'],
                         publishedAt = video['snippet']['publishedAt'],
                         viewCount = video['statistics']['viewCount'],
                         likeCount = 0,
                         commentCount = 0
                         )
            # Append the video statistics to the list
            videoStatsList.append(videoStats)
    # Return the list of video statistics
    return videoStatsList



# Function to get key insights of the video it takes pandas dataframe as parameter
def get_key_insights(videoData):
    # Find the most viewed video
    mostViewed = videoData.nlargest(1, 'viewCount')
    mostViewedVideo = mostViewed.iloc[0]['title']
    mostViewedVideoId = mostViewed.iloc[0]['videoId']
    viewsMv = mostViewed.iloc[0]['viewCount']
    
    # Find the least viewed video
    leastViewed = videoData.nsmallest(1, 'viewCount')
    leastViewedVideo = leastViewed.iloc[0]['title']
    leastViewedVideoID = leastViewed.iloc[0]['videoId']
    viewsLv =  leastViewed.iloc[0]['viewCount']
    
    # Find the most liked video
    mostLiked = videoData.nlargest(1, 'likeCount')
    mostLikedVideo = mostLiked.iloc[0]['title']
    mostLikedVideoID = mostLiked.iloc[0]['videoId']
    likesMl = mostLiked.iloc[0]['likeCount']

    
    # Find the least liked video
    leastLiked = videoData.nsmallest(1, 'likeCount')
    leastLikedVideo = leastLiked.iloc[0]['title']
    leastLikedVideoID = leastLiked.iloc[0]['videoId']
    likesLl = leastLiked.iloc[0]['likeCount']
    # Find the most engaging video
    mostengaging = videoData.nlargest(1,'engagementRate')
    mostengagingVideo = mostengaging.iloc[0]['title']
    mostengagingVideoID = mostengaging.iloc[0]['videoId']
    me = mostengaging.iloc[0]['engagementRate']
    # Return the insights in the form of tuple
    return mostViewedVideo, mostViewedVideoId, viewsMv , leastViewedVideo, leastViewedVideoID, viewsLv , mostLikedVideo, mostLikedVideoID, likesMl, leastLikedVideo, leastLikedVideoID, likesLl, mostengagingVideo, mostengagingVideoID, me




# defining a main functions
def main():

# Create a container for the UI elements
    with st.container():
        # Create two columns
        c1, c2 = st.columns((1,2))
        with c1:
            # Add a title and instructions for the user
            st.title("Youtube Channel Analyzer")
            st.write('Enter any youtube channel Id and get key details ')
            st.write('')
            st.write('--- Details included ---  ')
            st.write('Most Liked Video, Most Engaging Video, Least Viewed Video etc.')
            st.write('')
            # Add a link to the source code and the name of the creator
            st.write('View [source code](https://github.com/r7rahuls/CropRecommender_jupyterNotebook.git)')
            st.write("This Project was created by [Rahul Singh](https://www.linkedin.com/in/r7rahuls)")
            st.write('')
            st.write('')
            st.write('')
            st.write('Scroll down to try it out')
            

            # displaying the animation in second column of the container
            with c2:
                st_lottie(utubeIcon, height = 550, key="youtubeIcon")


    with st.container():
        channelName = ''
        videoCount = ''
        subscriberCount = '' 
        CviewCount = ''
        channelImg = 'https://yt3.ggpht.com/nZtFADYYiaJhlfM9H0ZHjTzvfg_bQzs1Liuw9nVhUGQ6qocyoJCt-wm5hMPo2CVzF8L2juJ25g=s240-c-k-c0x00ffffff-no-rj'
        mostViewedVideo = ''
        mostViewedVideoId = ''
        viewsMv = 0
        leastViewedVideo = ''
        leastViewedVideoID = ''
        viewsLv = 0
        mostLikedVideo = ''
        mostLikedVideoID = ''
        likesMl = 0
        leastLikedVideo = ''
        leastLikedVideoID = ''
        likesLl = 0
        mostengagingVideo = ''
        mostengagingVideoID = ''
        me = 0
        # Create a text input field for the user to enter a YouTube channel ID
        channel_id = st.text_input("Enter Youtube Channel Id")
        # Create a button that, when clicked, will execute the rest of the code
        if st.button("Get Details"):

            channelName, videoCount, subscriberCount, CviewCount, playlistId, channelImg = get_channel_statistics(youtube, channel_id)
            videoIds =  get_video_ids(youtube, playlistId)
            videoStatsList = get_video_details(youtube, videoIds)
            videoData = pd.DataFrame(videoStatsList)
            videoData['videoId'] = videoIds
            #Modifying the dataframe
            videoData['publishedAt'] = pd.to_datetime(videoData['publishedAt']).dt.date
            videoData['viewCount'] = pd.to_numeric(videoData['viewCount'])

            videoData['likeCount'] = pd.to_numeric(videoData['likeCount'])
            videoData['commentCount'] = pd.to_numeric(videoData['commentCount'])
            # adding a new column 'engagementRate'
            videoData['engagementRate'] = ((videoData['likeCount']+videoData['commentCount'])/videoData['viewCount'])*100
            videoData = videoData.replace([np.inf, -np.inf], np.nan)
            videoData = videoData.dropna()
            mostViewedVideo, mostViewedVideoId, viewsMv , leastViewedVideo, leastViewedVideoID, viewsLv, mostLikedVideo, mostLikedVideoID,likesMl, leastLikedVideo, leastLikedVideoID, likesLl, mostengagingVideo, mostengagingVideoID, me = get_key_insights(videoData)



            # Show a message that the analysis is done
            st.balloons()
            st.success("Analysis Done!")


        
        col1, col2, col3, col4, col5 = st.columns((1,0.25,0.8,2,0.5))
        with col1:
            st.write('')
            st.write('')
            st.write('')
            st.image(channelImg, width=200)
            st.write('')
            st.write('')
            st.write('Channel Name -  '+channelName) 
            st.write('Total Subscribers -  '+subscriberCount)
            st.write('Total Videos -  '+videoCount)
            st.write('Total Views -  '+CviewCount) 



        with col3:
            st.write('')
            st.write('')
            st.write('')
            st.write('Most viewed Video')
            st.write('')
            st.write('')
            st.write('Least viewed Video')
            st.write('')
            st.write('')
            st.write('Most Liked Video')
            st.write('')
            st.write('')
            st.write('Least Liked Video')
            st.write('')
            st.write('')
            st.write('Most Engaging Video')
            st.write('')
            st.write('')
        
        with col4:
            st.write('')
            st.write('')
            st.write('')
            st.write(f"[{mostViewedVideo}](https://www.youtube.com/watch?v={mostViewedVideoId})")
            st.write('')
            st.write('')
            st.write(f"[{leastViewedVideo}](https://www.youtube.com/watch?v={leastViewedVideoID})")
            st.write('')
            st.write('')
            st.write(f"[{mostLikedVideo}](https://www.youtube.com/watch?v={mostLikedVideoID})")
            st.write('')
            st.write('')
            st.write(f"[{leastLikedVideo}](https://www.youtube.com/watch?v={leastLikedVideoID})")
            st.write('')
            st.write('')
            st.write(f"[{mostengagingVideo}](https://www.youtube.com/watch?v={mostengagingVideoID})")
            st.write('')
            st.write('')

        with col5:
            st.write('')
            st.write('')
            st.write('')
            st.write(str(viewsMv)+' Views')
            st.write('')
            st.write('')
            st.write(str(viewsLv)+' Views')
            st.write('')
            st.write('')
            st.write(str(likesMl)+' Likes')
            st.write('')
            st.write('')
            st.write(str(likesLl)+' Likes')
            st.write('')
            st.write('')
            st.write(f'{me:.2f}'+" %")
            st.write('')
            st.write('')
            
    



#if __name__ == '__main__':
main()
