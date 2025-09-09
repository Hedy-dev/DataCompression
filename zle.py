def zle_encode(data):
    result = []
    i = 0
    while i < len(data):
        if data[i] != 0:
            if data[i] in [254, 255]:
                result.extend([0, data[i]])  # Экранируем 254 и 255
            else:
                result.append(data[i])
            i += 1
        else:
            # Подсчет длины последовательности нулей
            zero_count = 0
            while i < len(data) and data[i] == 0:
                zero_count += 1
                i += 1

            # Кодируем число zero_count + 1 в двоичном виде (без первой 1)
            binary = bin(zero_count + 1)[3:]  # Пропускаем первую 1
            for b in binary:
                result.append(254 if b == '0' else 255)
    return result

def zle_decode(data):
    result = []
    i = 0
    while i < len(data):
        if data[i] == 0:
            if i + 1 >= len(data):
                raise ValueError("Неправильное экранирование 254/255")
            result.append(data[i + 1])  # Восстанавливаем 254 или 255
            i += 2
        elif data[i] in [254, 255]:
            # Читаем последовательность битов
            bits = ""
            while i < len(data) and data[i] in [254, 255]:
                bits += '0' if data[i] == 254 else '1'
                i += 1
            n = int("1" + bits, 2) - 1  # Восстанавливаем длину нулей
            result.extend([0] * n)
        else:
            result.append(data[i])
            i += 1
    return result