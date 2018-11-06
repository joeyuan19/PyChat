USER_COLLECTION = [
    {
        '_id': 'user@useremail.com',
        'first_name': '',
        'last_name': '',
        'password': '',
        'time_created': '',
        'time_active': '',

        'conversation_list': [
            {"_id": "ConversationID"},
            {"_id": "ConversationID"},
            {"_id": "ConversationID"},
        ]
    },
]

CONTEXT_COLLECTION = [
    {
        "_id": "http://www.theverge.com/2014/7/11/5886887/aes-f-liminal-space-trilogy-interview",
        "context_type": "article",
        "time_retrieved": "May 4, 2014",
        "category": "techonology",
        "views": "22032",
        "shares": "131",
        "img": "static/img/1.png",
        "domain": "www.theverge.com",
        "url": "http://www.theverge.com/2014/7/11/5886887/aes-f-liminal-space-trilogy-interview",
        "description": "In one room, a shirtless, redheaded boy is about to drive his sword through the stomach of a child on a snowcapped mountain. In another, statuesque models lounge on a digital beach as a hurricane...",
        "conversation_list": [
            {"_id": "ConversationID"},
            {"_id": "ConversationID"},
            {"_id": "ConversationID"}
        ],
        "highlight_list": [
            {"_id": "Highlight ID"},
            {"_id": "Highlight ID"},
            {"_id": "Highlight ID"},
            {"_id": "Highlight ID"},
        ]
    },
]

CONVERSATION_COLLECTION = [
    {
        "_id": "MongoAutoGen",
        "time_created": "May 2, 2013",
        "time_updated": "May 23, 2013",
        "unread_messeges": "True/False",
        "scope": "public",
        "initial_context": {"_id": "http://www.theverge.com/2014/7/11/5886887/aes-f-liminal-space-trilogy-interview"},
        "context_list": [
            {"_id": "www.wewewewe.com"},
            {"_id": "www.sdsdsd.com"},
        ],
        "participants": [
            {"_id": "avatchinsky@outlook.com"},
            {"_id": "yuan@gmail.com"},
        ],
        "msgs": [
            {"_id": "msg-00000000000001"},
            {"_id": "msg-00000000000002"},
            {"_id": "msg-00000000000003"},
            {"_id": "msg-00000000000004"},
            {"_id": "msg-00000000000005"},
        ]
    }
]

HIGHLIGHT_COLLECTION = [
    {
        "_id": "dsdsdsdsds",
        "messege_id": "Messege ID",
        "time_created": "May 2, 2013",
        "start_indx": "34",
        "end_idnx": "54",
        "response": "1" # or -1
    }
]

MESSEGE_COLLECTION = [
    {
        "_id": "MongoAutoGen",
        "time_created": "May 2, 2013",
        "conversation": "Conversation ID",
        "read": "True / False",
        "author": {"_id": "avatchinsky"},
    }
]
