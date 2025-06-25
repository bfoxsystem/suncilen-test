import asyncio
import websockets
import json
from keep_alive import keep_alive
keep_alive()

def smart_predict(history):
    if len(history) < 10:
        return "📉 Chưa đủ dữ liệu để dự đoán.", None

    # Phân tích chuỗi gần nhất
    last_10 = history[-10:]
    tai_xiu = ["TÀI" if v >= 11 else "XỈU" for v in last_10]

    # Trọng số từ gần → xa: 10,9,...,1
    weights = list(range(10, 0, -1))
    score = {"TÀI": 0, "XỈU": 0}
    for i in range(10):
        score[tai_xiu[i]] += weights[i]

    # Phân tích chuỗi liên tiếp
    last_result = tai_xiu[-1]
    streak = 1
    for i in range(len(tai_xiu)-2, -1, -1):
        if tai_xiu[i] == last_result:
            streak += 1
        else:
            break

    # Nếu chuỗi T/X >= 4 lần → khả năng đảo chiều cao
    if streak >= 4:
        predicted = "XỈU" if last_result == "TÀI" else "TÀI"
        return f"🔁 Chuỗi {streak} {last_result} → Đảo chiều dự đoán: {predicted}", predicted

    # Nếu chênh lệch điểm lớn → nghiêng về bên mạnh
    if abs(score["TÀI"] - score["XỈU"]) >= 12:
        predicted = "TÀI" if score["TÀI"] > score["XỈU"] else "XỈU"
        return f"📊 Trọng số nghiêng mạnh về: {predicted}", predicted

    # Phát hiện cầu bẫy: xen kẽ liên tục
    pattern = "".join(["T" if v == "TÀI" else "X" for v in tai_xiu[-6:]])
    bait_patterns = ["TXT", "XTX", "TXXT", "XTTX"]
    if any(p in pattern for p in bait_patterns):
        predicted = "TÀI" if last_result == "XỈU" else "XỈU"
        return f"🪤 Phát hiện cầu bẫy ({pattern}) → Đảo ngược kết quả: {predicted}", predicted

    # Ngược lại chọn theo điểm cao hơn
    predicted = "TÀI" if score["TÀI"] > score["XỈU"] else "XỈU"
    return f"🧠 Tổng điểm: TÀI={score['TÀI']}, XỈU={score['XỈU']} → Dự đoán: {predicted}", predicted
    
async def sunwin_client():
    url = "ws://157.245.59.82:8000/game_sunwin/ws?id=duy914c&key=dduy1514nsadfl"
    history = []
    predicted_result = None
    predicted_round = None

    async with websockets.connect(url) as websocket:
        print("🌐 Đã kết nối tới máy chủ Sunwin!")

        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)

                if isinstance(data, dict) and "Tong" in data:
                    dice1 = data.get("Xuc_xac_1", "?")
                    dice2 = data.get("Xuc_xac_2", "?")
                    dice3 = data.get("Xuc_xac_3", "?")
                    dice_sum = data["Tong"]
                    result = "TÀI" if dice_sum >= 11 else "XỈU"
                    round_id = data.get("Phien", "???")

                    print(f"\n🎲 [Phiên {round_id}] 🎲")
                    print(f"🎯 Xúc xắc: [{dice1}, {dice2}, {dice3}] → Tổng: {dice_sum} → Kết quả: {result}")

                    # Kiểm tra dự đoán trước đó
                    if predicted_result is not None and predicted_round == round_id:
                        if predicted_result == result:
                            print(f"✅ Dự đoán đúng! ({predicted_result})")
                        else:
                            print(f"❌ Dự đoán sai! (Dự đoán: {predicted_result}, Thực tế: {result})")
                        print("🔄 Đang chờ đủ dữ liệu để dự đoán tiếp...")
                        predicted_result = None
                        predicted_round = None

                    # Cập nhật lịch sử
                    history.append(dice_sum)

                    # Nếu đủ dữ liệu thì dự đoán phiên kế tiếp
                    if len(history) >= 5 and predicted_result is None:
                        predict_text, predicted_result = smart_predict(history)
                        predicted_round = round_id + 1 if isinstance(round_id, int) else "???"
                        print(f"\n📌 {predict_text}")
                        print(f"🔮 Dự đoán cho phiên tiếp theo ({predicted_round}): {predicted_result}")
                        print("-" * 40)

                else:
                    print("⚠️ Dữ liệu không hợp lệ hoặc thiếu 'Tong'")

            except Exception as e:
                print(f"🚨 Lỗi: {e}")
                await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(sunwin_client())