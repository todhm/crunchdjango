import json 

def add_recommendation_data(botoclient,userdata,tracking_id):
    if not userdata.get("ITEM_ID") or not userdata.get("USER_ID"):
        raise ValueError
    putEventProperties =  json.dumps({"itemId": str(userdata['ITEM_ID']) })
    botoclient.put_events(
            trackingId=tracking_id,
            userId=userdata['USER_ID'],
            sessionId='1',
            eventList=[
                {   
                    "sentAt": userdata['TIMESTAMP'],
                    "eventType": userdata['EVENT_TYPE'],
                    "properties":  putEventProperties,
                }
    ])

def get_recommendation_goods(botoclient,user_id,item_id,campaign_arn):
    response = botoclient.get_recommendations(
            campaignArn=campaign_arn,
            userId=user_id,
            itemId=item_id,
            numResults=25
    )
    item_id_list = response.get('itemList')
    item_id_list = [ int(x['itemId']) for x in item_id_list]
    return item_id_list
