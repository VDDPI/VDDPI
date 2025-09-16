# Output:
def run_svm(data):
    from libsvm.svmutil import svm_train
    y, x  = svm_read_problem_from_data(data["data"].replace('\\n', '\n'))
    return svm_train(y, x, '-s 0 -t 2 -d 3 -g 0.5 -r 0 -n 0.5 -m 100 -c 5 -e 0.1 -p 0.1 -h 1 -b 0')