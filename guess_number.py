import random

print("=" * 40)
print("猜数字小游戏")
print("=" * 40)

while True:
    answer = random.randint(1, 100)
    count = 0
    print("\n我已经想好了一个1-100之间的整数，快来猜猜吧！")

    while True:
        try:
            guess = int(input("\n请输入你猜的数字: "))
            count += 1

            if guess < 1 or guess > 100:
                print("请输入1-100之间的数字！")
                continue

            if guess < answer:
                print("偏小了！再试一次")
            elif guess > answer:
                print("偏大了！再试一次")
            else:
                print(f"恭喜你猜对了！答案就是 {answer}")
                print(f"你一共猜了 {count} 次")
                break

        except ValueError:
            print("错误：请输入有效的整数！")

    play_again = input("\n是否重新开始游戏？(y/n): ").lower()
    if play_again != 'y':
        print("游戏结束，感谢参与！")
        break
