#include <unordered_map>
#include <vector>
using namespace std;

class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        // valueToIndex[value] 表示这个数此前出现的位置。
        unordered_map<int, int> valueToIndex;

        for (int i = 0; i < static_cast<int>(nums.size()); ++i) {
            int needed = target - nums[i];
            auto it = valueToIndex.find(needed);

            if (it != valueToIndex.end()) {
                return {it->second, i};
            }

            valueToIndex[nums[i]] = i;
        }

        return {};
    }
};
