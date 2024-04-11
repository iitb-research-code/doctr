import argparse

from sklearn.model_selection import train_test_split
import os
import random

from doctr.datasets import VOCABS

class SmallPreprocessWordDataset:
    def __init__(self, input_file, valid_vocab):
        self.input_file = input_file
        self.valid_vocab = valid_vocab

    def load_file_as_words(self):

        with open(self.input_file, encoding="utf-8") as f:
            data = f.read()
        
        words = list(map(lambda x: x.strip(),data.split()))
        return words
    
    def filter_words(self, words):

        filtered_words = []

        for word in words:
            include = True
            for i in word:
                if i not in self.valid_vocab:
                    include = False
            if include:
                filtered_words.append(word)
        
        return filtered_words
    
    def split_data(self, words):
        return train_test_split(words, test_size = 0.1, random_state= 24)

    def __call__(self, out_dir, sample = None, unique = False, continue_check = False):
        words = self.load_file_as_words()
        print(f"There are totally {len(words)} words in the file.")
        filtered = self.filter_words(words)
        print(f"There are totally {len(filtered)} valid words in the file.")

        if unique:
            filtered = list(set(filtered))
            print(f"There are totally {len(filtered)} unique valid words in the file.")
        if sample:
            filtered = random.sample(filtered, int(len(filtered) * sample))
            print(f"Sampled only {len(filtered)} random words from data.")

        if continue_check:
            c = input("Do you want to save?(y/n)")
            if c!="y":
                return
        train, val = self.split_data(filtered)

        train = "\n".join(train)
        val = "\n".join(val)

        if not os.path.exists(out_dir):
            os.mkdir(out_dir)        

        try:
            with open(os.path.join(out_dir,"train.txt"),"w",encoding="utf-8") as f:
                f.write(train)
            with open(os.path.join(out_dir,"val.txt"),"w",encoding="utf-8") as f:
                f.write(val)

            print(f"The processed words for given vocabulary is stored in {out_dir} as train.txt and val.txt")
        except:
            raise "Unable to Create File. Failed"

class PreprocessWordDataset:
    def __init__(self, input_file, valid_vocab):
        self.input_file = input_file
        self.valid_vocab = valid_vocab
    
    def filter_words(self, words):

        filtered_words = []

        for word in words:
            include = True
            for i in word:
                if i not in self.valid_vocab:
                    include = False
            if include:
                filtered_words.append(word)
        
        return filtered_words
    
    def get_words(self, data):
        words = list(map(lambda x: x.strip(),data.split()))
        return words
    
    def split_data(self, words, test_size):
        if len(words) <= 1:
            return random.choice([(words,[]),([],words)])
        return train_test_split(words, test_size = test_size, random_state= 24)
    
    def __call__(self, output_path, continue_ptr, test_size = 0.1):
        if not os.path.exists(output_path):
            os.mkdir(output_path)
            
        try:
            infile = open(self.input_file, encoding="utf-8")
            if continue_ptr:
                infile.seek(continue_ptr)
                print(f"Resuming from file location {continue_ptr}")
            
            mode = "w"
            if os.path.isfile(os.path.join(output_path,"train.txt")):
                mode = "a"
            trainfile = open(os.path.join(output_path,"train.txt"),mode,encoding="utf-8")
            mode = "w"
            if os.path.isfile(os.path.join(output_path,"val.txt")):
                mode = "a"
            valfile = open(os.path.join(output_path,"val.txt"),mode,encoding="utf-8")
            in_count, train_count, val_count = 0,0,0
            tolerate = 0
            try:
                i = 0
                while True:
                    buffer = infile.readline()
                    words = self.get_words(buffer)
                    if not words:
                        tolerate += 1
                        if tolerate >= 10:
                            break
                    else:
                        tolerate = 0
                    in_count += len(words)

                    filtered = self.filter_words(words)
                    train, val = self.split_data(filtered, test_size)
                    train_count += len(train)
                    val_count += len(val)

                    trainfile.write("\n".join(train) + "\n")
                    if val:
                        valfile.write("\n".join(val) + "\n")

                    if i%100 == 0:
                        print(f"Input Words: {in_count} | Train Words: {train_count} | Val Words: {val_count}")
                    
                    i += 1

            except EOFError:
                print("File End reached")
            finally:
                print(f"""
Processed Input words: {in_count}
Train Split: {train_count} words
Val Split: {val_count} words
""")


        except Exception as e:
            print("Error Opening the files.")
        
        except KeyboardInterrupt:
            print("Terminated Preprocessing")
            print(f"Final file pointer at {infile.tell()}")
        
        finally:
            infile.close()
            trainfile.close()
            valfile.close()



def main(args):
    valid_vocab = VOCABS['tamil']
    preprocess = PreprocessWordDataset(args.input_path,valid_vocab)
    # preprocess(args.output_path, sample = args.sample, unique=args.unique, continue_check=args.continue_check)
    preprocess(args.output_path, args.continue_ptr, args.test_size)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess Data")
    parser.add_argument("--input_path", type=str, help="Path to input data")
    parser.add_argument("--output_path", type=str, help="Path to output directory")
    parser.add_argument("--vocab", type=str, help="vocab key in VOCAB dictionary")
    # parser.add_argument("--sample", type=float, help="Sample value")
    parser.add_argument("--test_size", type=float, help="Validation set split ratio")
    parser.add_argument("--continue_ptr", type=int, help="File Pointer to continue", default= 0)
    # parser.add_argument("--unique", action="store_true", help="Filter only unique words")
    # parser.add_argument("--continue_check", action="store_true", help="If set then ask before saving the data.")
    args = parser.parse_args()
    
    main(args)