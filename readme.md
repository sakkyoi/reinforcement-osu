# Reinforcement OSU
Still in experiment. Do not use it in production.

The way to get the status of osu! is to access the memory of the osu! process. The address and pointer of the memory are obtained from the [ProcessMemoryDataFinder](https://github.com/Piotrekol/ProcessMemoryDataFinder)

## License
This project is licensed under the LGPL-3.0 License - see the [LICENSE](LICENSE) file for details

## Acknowledgments
* [qsu](https://github.com/baballev/qsu) - The idea of to use reinforcement learning to play osu!
* [ProcessMemoryDataFinder](https://github.com/Piotrekol/ProcessMemoryDataFinder) - The idea of using the memory of the osu! process to get the status of the game and the address and pointer of the memory

some notes (Mandarin):
滑鼠疑似動太快，而不會移動
正確原因是，osu不能打開原生輸入(Raw Input)

另外獲取座標的方式不能每次都用pid重抓一次，因為遊戲內和主程式的pid不一樣，而主程式被隱藏後，座標會直接偏離(解決方法：開始前儲存座標軸，開始後不要移動視窗(其實也沒機會移動啦))

skin: https://osu.ppy.sh/community/forums/topics/656939?n=1
細節設定、打擊閃光關閉(https://forum.gamer.com.tw/C.php?bsn=18601&snA=8060)

# 我的enviroment好像寫得不太對，