#ifndef STATEMACHINE_HPP
#define STATEMACHINE_HPP

#include "Arduino.h"
#include <map>

class State;
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
};

class Model {
public:
    Model(){
        Serial.println("Create Model");
    }
    void set_event(const Event *event) {
        m_event = event;
    }
    const Event* run(State state) {
        Serial.println("Model::run");
        while (m_event == nullptr) {
            vTaskDelay(500/portTICK_PERIOD_MS);
        }
        return m_event;
    }
protected:
    const Event *m_event = nullptr;
};

class Event {
    public:
        Event(std::string name) : m_name(name) {}
        void set_new_model(Model* model) {
            m_kv["new_model"] = model;
        }
        Model* clear_new_model() const {
            auto it = m_kv.find("new_model");
            if (it != m_kv.end()) {
                return it->second;
            } else {
                return nullptr;
            }
        }
        std::string m_name;
    private:
        std::map<std::string, Model*> m_kv;
};

class Transition {
    public:
        Transition(const Event trigger, const State source, const State destination) : m_trigger(trigger), m_source(source), m_destination(destination) {}
        const Event m_trigger;
        const State m_source;
        const State m_destination;
};

class StateMachine {
public:
    StateMachine(){}
    StateMachine(Model &model, Transition *transitions, uint8_t transitions_size, const State initial_state) : 
        m_model(model), m_transitions(transitions), m_transitions_size(transitions_size), m_state(initial_state) {
        Serial.println("constructor StateMachine");
    }
    
    void set_new_model(Model &new_model) {
        m_model = new_model;
    }

    void start() {
        while (true) {
            Serial.printf("StateMachine Model::run with state: %s\n", m_state.m_name.c_str());
            const Event* new_event = m_model.run(m_state);
            Serial.printf("model run finished, new_event: %s\n", *new_event->m_name.c_str());
            for (uint8_t i = 0; i < m_transitions_size; i++) {
                if (m_transitions[i].m_trigger.m_name == new_event->m_name && m_transitions[i].m_source.m_name == m_state.m_name) {
                    Serial.printf("new_event: %s, transition_source: %s, transition.destination: %s\n", new_event->m_name.c_str(), m_transitions[i].m_source.m_name.c_str(), m_transitions[i].m_destination.m_name.c_str());
                    m_state = m_transitions[i].m_destination;
                    Model* new_model = new_event->clear_new_model();
                    if (new_model != nullptr) {
                        m_model = *new_model;
                    }
                    break;
                }
            }
        }
    }
private:
    Model m_model;
    Transition *m_transitions;
    uint8_t m_transitions_size;
    State m_state;
};

#endif