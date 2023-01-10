#ifndef STATEMACHINE_HPP
#define STATEMACHINE_HPP

#include "Arduino.h"
#include <map>

class Model;
class Event;
class Transition;

class State {
    public:
        State() {}
        State(std::string name) : m_name(name) {}
        std::string m_name;
        friend bool operator==(const State& lhs, const State& rhs) {
            return lhs.m_name == rhs.m_name;
        }
        bool equals(State *otherState) {
            return m_name == otherState->m_name;
        }
};

class Model {
public:
    Model() {
        Serial.println("create model");
    }

    void set_event(Event *ptr_event) {
        Serial.println("set event");
        m_ptr_event = ptr_event;
    }
    
    virtual Event* run(State *ptr_state);
protected:
    Event *m_ptr_event;
};

class Event {
    public:
        Event(std::string name) : m_name(name) {}
        void set_new_model(Model* model) {
            m_kv["new_model"] = model;
        }
        
        Model* clear_new_model() {
            auto it = m_kv.find("new_model");
            if (it != m_kv.end()) {
                return it->second;
            } else {
                return nullptr;
            }
        }
        
        bool equals(Event *otherEvent) {
            return m_name == otherEvent->m_name;
        }

        std::string m_name;
    private:
        std::map<std::string, Model*> m_kv;
};

Event* Model::run(State* ptr_state) {
    Serial.println("Model::run outside class");
    while(m_ptr_event == nullptr) {
        Serial.println("no event -> sleeping");
        vTaskDelay(500/portTICK_PERIOD_MS);
    }
    return m_ptr_event;    
}

class Transition {
    public:
        Transition(Event *trigger, State *source, State *destination) : m_ptr_trigger(trigger), m_ptr_source(source), m_ptr_destination(destination) {}
        Event *m_ptr_trigger;
        State *m_ptr_source;
        State *m_ptr_destination;
};

class StateMachine {
public:
    StateMachine(){
        Serial.println("default constructor StateMachine");
    }
    StateMachine(Model *model, Transition *transitions, uint8_t transitions_size, State *initial_state) : 
        m_ptr_model(model), m_ptr_transitions(transitions), m_transitions_size(transitions_size), m_ptr_state(initial_state) {
        Serial.println("parameter constructor StateMachine");
    }
    
    void start() {
        while (true) {

            Serial.printf("StateMachine Model::run with state: %s\n", m_ptr_state->m_name.c_str());
            Event* ptr_new_event = m_ptr_model->run(m_ptr_state);
            Serial.printf("model run finished, new_event: %s\n", ptr_new_event->m_name.c_str());

            for (uint8_t i = 0; i < m_transitions_size; i++) {

                if (m_ptr_transitions[i].m_ptr_trigger->equals(ptr_new_event) && m_ptr_transitions[i].m_ptr_source->equals(m_ptr_state)) {

                    Serial.printf("new_event: %s, transition_source: %s, transition.destination: %s\n", 
                        ptr_new_event->m_name.c_str(), m_ptr_transitions[i].m_ptr_source->m_name.c_str(), m_ptr_transitions[i].m_ptr_destination->m_name.c_str());

                    m_ptr_state = m_ptr_transitions[i].m_ptr_destination;

                    Model* new_model = ptr_new_event->clear_new_model();
                    if (new_model != nullptr) {
                        Serial.println("setting new model");
                        m_ptr_model = new_model;
                    }

                    break;
                }
            }
        }
    }

private:
    Model* m_ptr_model;
    Transition* m_ptr_transitions;
    uint8_t m_transitions_size;
    State* m_ptr_state;
};

#endif