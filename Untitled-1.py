def show_menu():
    print("\n" + "=" * 40)
    print("       单词大小写转换工具")
    print("=" * 40)
    print("1. 全部大写 (UPPERCASE)")
    print("2. 全部小写 (lowercase)")
    print("3. 首字母大写 (Capitalize)")
    print("0. 退出程序")
    print("=" * 40)

def convert_text(text, choice):
    if choice == '1':
        return text.upper()
    elif choice == '2':
        return text.lower()
    elif choice == '3':
        return text.capitalize()
    else:
        return None

def main():
    print("\n欢迎使用单词大小写转换工具！")
    
    while True:
        text = input("\n请输入要转换的英文单词或句子: ").strip()
        
        if not text:
            print("输入不能为空，请重新输入！")
            continue
        
        while True:
            show_menu()
            choice = input("请选择转换类型 (0-3): ").strip()
            
            if choice == '0':
                print("\n感谢使用，再见！")
                return
            
            if choice in ['1', '2', '3']:
                result = convert_text(text, choice)
                print(f"\n转换结果: {result}")
                break
            else:
                print("无效选择，请输入 0-3 之间的数字！")
        
        while True:
            continue_choice = input("\n是否继续转换其他内容？(y/n): ").strip().lower()
            if continue_choice == 'n':
                print("\n感谢使用，再见！")
                return
            elif continue_choice == 'y':
                break
            else:
                print("请输入 y 或 n！")

if __name__ == "__main__":
    main()