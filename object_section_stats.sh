#!/bin/bash

# 配置编译器工具链路径
OBJDUMP="/opt/Xuantie-900-gcc-elf-newlib-x86_64-V2.10.2/bin/riscv64-unknown-elf-objdump"

# 默认参数
MODE="hex"
SECTION=""
TOTAL=0
FILES=()

# 解析参数
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --dec) MODE="dec"; shift ;;
        --hex) MODE="hex"; shift ;;
        -s|--section) SECTION="$2"; shift 2 ;;
        *) FILES+=("$1"); shift ;;
    esac
done

# 参数检查
if [ -z "$SECTION" ] || [ ${#FILES[@]} -eq 0 ]; then
    echo "用法: $0 -s <section_name> [--dec|--hex] <files_pattern>"
    echo "示例: $0 -s .ram_text \"obj/subsys/**/*.o\""
    exit 1
fi

echo -e "\nTarget Section: \033[1;33m$SECTION\033[0m"
echo -e "----------------------------------------------------------------------"
printf "%-12s | %s\n" "SIZE($MODE)" "FILENAME"
echo -e "----------------------------------------------------------------------"

# 处理所有匹配的文件
for pattern in "${FILES[@]}"; do
    for f in $pattern; do
        if [ -f "$f" ]; then
            # 提取指定 section 的 Size (objdump -h 输出的第3列)
            # 使用 awk 确保精确匹配段名，防止 .ram_text_init 匹配到 .ram_text
            raw_size=$($OBJDUMP -h "$f" 2>/dev/null | awk -v sec="$SECTION" '$2 == sec {print $3}')
            
            if [ ! -z "$raw_size" ]; then
                dec_size=$((16#$raw_size))
                TOTAL=$((TOTAL + dec_size))

                if [ "$MODE" == "dec" ]; then
                    printf "%-12d | %s\n" "$dec_size" "$f"
                else
                    printf "0x%-10s | %s\n" "$raw_size" "$f"
                fi
            fi
        fi
    done
done

echo -e "----------------------------------------------------------------------"
if [ "$MODE" == "hex" ]; then
    printf "\033[1;32mTOTAL: 0x%x (%d bytes)\033[0m\n\n" "$TOTAL" "$TOTAL"
else
    printf "\033[1;32mTOTAL: %d bytes\033[0m\n\n" "$TOTAL"
fi
