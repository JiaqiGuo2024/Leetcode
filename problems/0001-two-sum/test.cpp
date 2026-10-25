#include <cassert>
#include <iostream>
#include <vector>

#include "solution.cpp"

void checkAnswer(std::vector<int> nums, int target) {
    Solution solution;
    std::vector<int> answer = solution.twoSum(nums, target);

    assert(answer.size() == 2);
    assert(answer[0] != answer[1]);
    assert(answer[0] >= 0 && answer[0] < static_cast<int>(nums.size()));
    assert(answer[1] >= 0 && answer[1] < static_cast<int>(nums.size()));
    assert(nums[answer[0]] + nums[answer[1]] == target);
}

int main() {
    checkAnswer({2, 7, 11, 15}, 9);  // 普通样例
    checkAnswer({3, 2, 4}, 6);        // 不能重复使用下标 0
    checkAnswer({3, 3}, 6);           // 相同数、不同下标
    checkAnswer({-3, 4, 3, 90}, 0);  // 负数
    checkAnswer({0, 4, 3, 0}, 0);    // 两个零

    std::cout << "All tests passed.\n";
    return 0;
}
