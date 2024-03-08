from gptpy3.chat_client import ChatClient

client = ChatClient(name='gpt', openai_key_path="/home/user1/secret-key.txt", host='192.168.0.102', port=7788)
client.run()
# 172.23.38.211