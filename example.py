from gptpy3.chat_client import ChatClient

client = ChatClient(name='gpt', openai_key_path="/home/user1/secret-key.txt", host='192.168.0.100', port=7788)
client.run()
