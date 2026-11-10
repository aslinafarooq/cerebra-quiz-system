#include <iostream>
#include <cstring>

using namespace std;

struct Question {
    int id;
    char prompt[256];
    char options[4][128];
    int correct_option_index;
    double points;
    Question* next;
};

Question* head = nullptr;

void addQuestion(int id, const char* prompt, const char* oA, const char* oB, const char* oC, const char* oD, int correct, double points) {
    Question* newQ = new Question;
    newQ->id = id;
    strncpy(newQ->prompt, prompt, sizeof(newQ->prompt) - 1);
    strncpy(newQ->options[0], oA, sizeof(newQ->options[0]) - 1);
    strncpy(newQ->options[1], oB, sizeof(newQ->options[1]) - 1);
    strncpy(newQ->options[2], oC, sizeof(newQ->options[2]) - 1);
    strncpy(newQ->options[3], oD, sizeof(newQ->options[3]) - 1);
    newQ->correct_option_index = correct;
    newQ->points = points;
    newQ->next = nullptr;

    if (!head) {
        head = newQ;
        return;
    }
    Question* curr = head;
    while (curr->next) {
        curr = curr->next;
    }
    curr->next = newQ;
}

void init_questions() {
    if (head != nullptr) return;
    addQuestion(1, "What is the Big O time complexity of Binary Search?", "O(n)", "O(log n)", "O(n^2)", "O(1)", 1, 10.0);
    addQuestion(2, "Which data structure operates on LIFO (Last-In, First-Out)?", "Queue", "Array", "Stack", "Linked List", 2, 10.0);
    addQuestion(3, "Which data structure manages student submissions in FIFO order?", "Stack", "Queue", "Tree", "Graph", 1, 10.0);
}

// CRITICAL: extern "C" prevents C++ name mangling so Python ctypes can find the symbols!
extern "C" {
    __declspec(dllexport) void process_attempt(const int* question_ids, const int* selected_opts, int count, double* out_score, double* out_total) {
        init_questions();
        double obtained = 0.0;
        double max_possible = 0.0;

        for (int i = 0; i < count; i++) {
            int q_id = question_ids[i];
            int sel_opt = selected_opts[i];

            Question* curr = head;
            while (curr) {
                if (curr->id == q_id) {
                    if (sel_opt == curr->correct_option_index) {
                        obtained += curr->points;
                    }
                    max_possible += curr->points;
                    break;
                }
                curr = curr->next;
            }
        }

        *out_score = obtained;
        *out_total = max_possible;
    }

    __declspec(dllexport) void add_custom_question(int id, const char* prompt, const char* oA, const char* oB, const char* oC, const char* oD, int correct, double points) {
        addQuestion(id, prompt, oA, oB, oC, oD, correct, points);
    }
}