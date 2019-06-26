#class to record all words given by skribblio

class Recorder:

    def getFile():
        return open("recorder/words.txt", "r+")

    def getWords():
        return Recorder.getFile().read().splitlines()

    def containsWord(word):
        return word in Recorder.getWords()

    def addWord(word):
        if not Recorder.containsWord(word):
            with open("recorder/words.txt", "a+") as file:
                file.write(word + "\n")

    def matchWords(length: int, hints: dict):
        matched_words = list()
        for word in Recorder.getWords():
            if len(word) != length:
                continue
            
            is_match = True
            for index in hints.keys():
                if word[index] != hints[index]:
                    is_match = False
                    break
                
            if is_match:
                matched_words.append(word)
                
        return matched_words
