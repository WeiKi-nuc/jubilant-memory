print("=" * 40)
print("简易四则运算计算器")
print("=" * 40)

while True:
    try:
        num1 = float(input("\n请输入第一个数字: "))
        num2 = float(input("请输入第二个数字: "))
        operator = input("请输入运算符 (+、-、*、/): ")

        if operator == '+':
            result = num1 + num2
        elif operator == '-':
            result = num1 - num2
        elif operator == '*':
            result = num1 * num2
        elif operator == '/':
            if num2 == 0:
                print("错误：除数不能为0！")
                continue
            result = num1 / num2
        else:
            print("错误：请输入有效的运算符（+、-、*、/）！")
            continue

        if num1 == int(num1):
            num1 = int(num1)
        if num2 == int(num2):
            num2 = int(num2)
        if result == int(result):
            result = int(result)

        print(f"\n{num1} {operator} {num2} = {result}")

        choice = input("\n是否继续计算？(y/n): ").lower()
        if choice != 'y':
            print("感谢使用计算器！")
            break

    except ValueError:
        print("错误：请输入有效的数字！")
    except Exception as e:
        print(f"发生未知错误：{e}")
