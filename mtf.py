def mtf_encode(text: str) -> list[int]:
    # используется фиксированный, заранее определенный алфавит (все байты от 0 до 255)
    alphabet = [chr(i) for i in range(256)]
    encoded_output = []
    for char in text:
        try:
            rank = alphabet.index(char)
        except ValueError:
            # символы не из диапазона
            raise ValueError(f"символ '{char}' не найден в фиксированном алфавите")
        encoded_output.append(rank)
        # Перемещаем символ в начало списка
        char_to_move = alphabet.pop(rank)
        alphabet.insert(0, char_to_move)
    return encoded_output

def mtf_decode(encoded_data: list[int]) -> str:
    # для декодирования нам нужен точно такой же начальный алфавит он заранее известен
    alphabet = sorted(list(set(chr(i) for i in range(256)))) 
    decoded_chars = []
    for rank in encoded_data:
        # символ по его номеру (индексу)
        char = alphabet[rank]
        decoded_chars.append(char)
        # реремещаем этот символ в начало алфавита
        char_to_move = alphabet.pop(rank)
        alphabet.insert(0, char_to_move)
    return "".join(decoded_chars)