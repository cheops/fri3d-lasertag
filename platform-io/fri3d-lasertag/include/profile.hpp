
#ifndef PROFILE_HPP
#define PROFILE_HPP

#include "Arduino.h"
#include <vector>

class Profile {
public:    
    Profile() {
        Serial.println("registering in c_children.");
        c_children.push_back(this);
    }

    static std::vector<Profile*> find_profiles() {
        return c_children;
    }
private:
    static std::vector<Profile*> c_children;

};

std::vector<Profile*> Profile::c_children;

#endif
