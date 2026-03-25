curl --request POST \
     --url https://api.heygen.com/v2/video/generate \
     --header 'accept: application/json' \
     --header 'content-type: application/json' \
     --header 'x-api-key: sk_V2_hgu_kCbQqUEj87I_6HxFZJklKESabhzQTIqUIDgmKujEgHZS' \
     --data '
{
  "caption": "false",
  "dimension": {
    "width": "720",
    "height": "1280"
  },
  "title": "test 123",
  "video_inputs": [
    {
      "character": {
        "type": "avatar",
        "scale": 1,
        "avatar_style": "normal",
        "talking_style": "stable",
        "avatar_id": "Annie_Casual_Standing_Front_2_public"
      },
      "voice": {
        "type": "text",
        "speed": "1",
        "pitch": "0",
        "elevenlabs_settings": {
          "model": "eleven_multilingual_v2"
        },
        "duration": "1",
        "voice_id": "65746ef1edd6420c8394628ea315c808",
        "input_text": "Object one. Dwójka dla spokojnej osoby."
      },
      "background": {
        "type": "color",
        "value": "#FFFFFF",
        "play_style": "freeze",
        "fit": "cover",
        "image_asset_id": "14d8d0552a844734b300731d462386d0",
        "url": "https://resource2.heygen.ai/image/14d8d0552a844734b300731d462386d0/original.jpg"
      },
      "text": {
        "type": "text",
        "text": "Dwójka dla spokojnej osoby w czystym domu 758 Londyn Do wynajęcia",
        "text_align": "center",
        "line_height": 2
      }
    },
    {
      "character": {
        "type": "avatar",
        "scale": 1,
        "avatar_style": "normal",
        "talking_style": "stable",
        "avatar_id": "Annie_Casual_Standing_Front_2_public"
      },
      "voice": {
        "type": "text",
        "speed": "1",
        "pitch": "0",
        "duration": "1",
        "voice_id": "65746ef1edd6420c8394628ea315c808",
        "input_text": "Object two.  W czystym domu."
      },
      "background": {
        "type": "image",
        "value": "#FFFFFF",
        "play_style": "freeze",
        "fit": "cover",
        "url": "https://assets.aws.londynek.net/images/ogl/1222/438662-202511142009-lg.jpg",
        "image_asset_id": "https://assets.aws.londynek.net/images/ogl/1222/438662-202511142009-lg.jpg"
      },
      "text": {
        "type": "text"
      }
    },
    {
      "character": {
        "type": "avatar",
        "scale": 1,
        "avatar_style": "normal",
        "talking_style": "stable",
        "avatar_id": "Annie_Casual_Standing_Front_2_public"
      },
      "voice": {
        "type": "text",
        "speed": "1",
        "pitch": "0",
        "duration": "1",
        "voice_id": "65746ef1edd6420c8394628ea315c808",
        "input_text": "Object three. Do wynajęcia w Londynie."
      },
      "background": {
        "type": "color",
        "value": "#FFFFFF",
        "play_style": "freeze",
        "fit": "cover"
      },
      "text": {
        "type": "text"
      }
    }
  ],
  "folder_id": "b3f8880ca61b4fa6abf445f0ce99b7d8"
}
'
