from ossapi import Ossapi
from ossapi.enums import GameMode
from dotenv import dotenv_values

class OSUAPI:
    def __init__(self):
        config = dotenv_values(".env")
        client_id = config["OSU_API_CLIENT_ID"]
        client_secret = config["OSU_API_CLIENT_SECRET"]
        self.api = Ossapi(client_id, client_secret)

    def get_beatmap_attributes(self, beatmap_id):
        return self.api.beatmap_attributes(beatmap_id = beatmap_id)
    
    def get_beatmap(self, beatmap_id):
        return self.api.beatmap(beatmap_id = beatmap_id)
    
    def get_beatmap_mode(self, beatmap_id):
        return self.get_beatmap(beatmap_id).mode
    

if __name__ == "__main__":
    api = OSUAPI()
    beatmap = api.get_beatmap_mode(beatmap_id=1852859)
    print(beatmap == GameMode.OSU)