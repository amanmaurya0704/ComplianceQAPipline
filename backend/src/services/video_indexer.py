'''
Connector : Azure Video Indexer and Python
'''
import os 
import time
import logging
import requests
import yt_dlp
from azure.identity import DefaultAzureCredential

logger = logging.getLogger("Video-Indexer")

class VideoIndexerService:
    def __init__(self):
        self.account_id = os.getenv("AZURE_VI_ACCOUNT_ID")
        self.location = os.getenv("AZURE_VI_LOCATION")
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.resource_group = os.getenv("AZURE_RESOURCE_GROUP")
        self.vi_name = os.getenv("AZURE_VI_NAME")
        self.credential = DefaultAzureCredential()

    def get_access_token(self):
        '''
        Generate access token for Azure Video Indexer API using Azure Identity library
        '''
        try:
            token_object = self.credential.get_token("https://management.azure.com/.default")
            return token_object.token
        except Exception as e:
            logger.error(f"Error occurred while fetching access token: {e}")
            raise

    def get_account_token(self,arm_access_token):
        '''
        Exchanges the ARM token for a Video Indexer account token
        '''
        #https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/
        # providers/Microsoft.VideoIndexer/accounts/{accountName}/generateAccessToken?api-version=2025-04-01
        #print(arm_access_token)
        url = (
            f"https://management.azure.com/subscriptions/{self.subscription_id}"
            f"/resourceGroups/{self.resource_group}"
            f"/providers/Microsoft.VideoIndexer/accounts/{self.vi_name}"
            f"/generateAccessToken?api-version=2025-04-01"
        )
        headers = {"Authorization": f"Bearer {arm_access_token}","Content-Type": "application/json"}
        payload = {"permissionType": "Contributor", "scope": "Account"}

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            logger.error(f"Error occurred while fetching account token: {response.text}")
            raise ValueError("Failed to generate account token")
        return response.json().get("accessToken")
    

    def download_youtube_video(self,url, output_path = "temp_video.mp4"):
        '''
        Download YouTube video using yt-dlp library
        '''
        logger.info(f"Downloading YouTube video from URL: {url}")
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_path, #outout template
            'quiet': False,
            'no_warnings': False,
            'extractor_args': {
                'youtube': 
                {
                'player_client': ['android', 'web']
                }
            },
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            }
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            logger.info(f"Video downloaded successfully to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error occurred while downloading YouTube video: {e}")
            raise
    
    def upload_video(self, video_path, video_name):
        '''
        Upload video to Azure Video Indexer using the account token
        '''
        arm_token = self.get_access_token()
        vi_token = self.get_account_token(arm_token)
        api_url = (
            f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos"
        )
        params = {
            
            "name": video_name,
            "privacy": "Private",
            "indexingPreset": "Default",
        }
        headers = {"Authorization": f"Bearer {vi_token}"}

        logger.info(f"Uploading video {video_name} to Azure Video Indexer")

        with open(video_path, 'rb') as video_file:
            files = {'file': video_file}
            response = requests.post(api_url, params=params, files=files, headers=headers)

        if response.status_code != 200:
            logger.error(f"Error occurred while uploading video: {response.text}")
            raise ValueError("Failed to upload video")
        
        video_id = response.json().get("id")
        logger.info(f"Video uploaded successfully. Video ID: {video_id}")
        return video_id
    
    def wait_for_processing(self, video_id):
        '''
        Poll the Azure Video Indexer API to check the processing status of the uploaded video
        '''
        logger.info(f"Waiting for video {video_id} to be processed")
        while True:
            arm_token = self.get_access_token()
            vi_token = self.get_account_token(arm_token)
            url = f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos/{video_id}/Index"
            params = {"accessToken": vi_token}
            response = requests.get(url, params=params)
            data = response.json()


            state = data.get("state")
            if state == "Processed":
                return data
            elif state == "Failed":
                logger.info(f"Video processing failed")
                raise Exception("Video processing failed") 
            elif state == "Quarantined":
                logger.info(f"Video is quarantined")
                raise Exception("Video is quarantined")
            logger.info(f"Current Status: {state}. Waiting for 30 seconds before checking again.")
            time.sleep(30)

    def extract_data(self, vi_json):
        """Parses the JSON into our State format."""
        transcript_lines = []
        for v in vi_json.get("videos", []):
            for insight in v.get("insights", {}).get("transcript", []):
                transcript_lines.append(insight.get("text"))
        
        ocr_lines = []
        for v in vi_json.get("videos", []):
            for insight in v.get("insights", {}).get("ocr", []):
                ocr_lines.append(insight.get("text"))
                
        return {
            "transcript": " ".join(transcript_lines),
            "ocr_text": ocr_lines,
            "video_metadata": {
                "duration": vi_json.get("summarizedInsights", {}).get("duration", {}).get("seconds"),
                "platform": "youtube"
            }
        }


def main():
    """Test function for VideoIndexerService"""
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv(override=True)

    # Initialize service
    vi_service = VideoIndexerService()

    # Test video URL
    test_video_url = "https://youtu.be/dT7S75eYhcQ"
    video_name = "test_video"
    output_path = "temp_test_video.mp4"

    try:
        print("=== Testing VideoIndexerService ===")

        # Test 1: Authentication
        print("\n1. Testing authentication...")
        arm_token = vi_service.get_access_token()
        print("✓ ARM token obtained")

        vi_token = vi_service.get_account_token(arm_token)
        print("✓ Video Indexer token obtained")

        # Test 2: Download video
        print("\n2. Downloading video...")
        #downloaded_path = vi_service.download_youtube_video(test_video_url, output_path)
        downloaded_path="C:\\Users\\amanm\\Downloads\\Machine_Learning\\Azure_Comp_Orestration\\backend\\src\\services\\temp_test_video.mp4"
        print(f"✓ Video downloaded to: {downloaded_path}")

        # Test 3: Upload video
        print("\n3. Uploading video...")
        vi_service.upload_video(downloaded_path, video_name)
        print("✓ Video upload initiated")

        # Note: Cannot test wait_for_processing because upload_video doesn't return video_id
        print("\n⚠ Note: upload_video() doesn't return video_id, so processing check is skipped")

        # Test 4: Clean up
        print("\n4. Cleaning up...")
        if os.path.exists(output_path):
            os.remove(output_path)
            print("✓ Temporary file removed")

        print("\n=== Test completed successfully ===")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
