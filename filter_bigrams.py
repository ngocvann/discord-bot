# filter_bigrams.py
# Lọc cụm từ 2 từ (bigram), bỏ cụm có dấu gạch ngang "-"

with open("bigramss.txt", "r", encoding="utf-8") as f, \
     open("bigrams.txt", "w", encoding="utf-8") as out:
    for line in f:
        phrase = line.strip().lower()
        if not phrase:
            continue
        words = phrase.split()
        # chỉ lấy cụm 2 từ, không chứa dấu "-"
        if len(words) == 2 and "-" not in phrase:
            out.write(phrase + "\n")

print("✅ Đã lọc xong! File bigrams.txt đã được tạo.")
