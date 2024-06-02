#ifndef STATEMACHINE_HPP
#define STATEMACHINE_HPP

#include "Arduino.h"

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
        bool equals(State* otherState) {
            return m_name == otherState->m_name;
        }
};

static portMUX_TYPE stateMachine_model_event_spinlock = portMUX_INITIALIZER_UNLOCKED;

class Model {
public:
    Model() {
        log_d("create model");
    }

    void set_event(Event* ptr_event);
    bool has_event();
    
    virtual Event* run(State* ptr_state);
private:
    Event* m_ptr_event;
};

class Event {
    public:
        Event(std::string name) : m_name(name) {}
        
        void set_new_model(Model* model) {
            m_new_model = model;
        }
        
        Model* clear_new_model() {
            Model* new_model = m_new_model;
            m_new_model = nullptr;
            return new_model;
        }
        
        bool equals(Event* otherEvent) {
            return m_name == otherEvent->m_name;
        }

        std::string m_name;
    private:
        Model* m_new_model;
};

Event* Model::run(State* ptr_state) {
    log_d("Model::run outside class");
    while(!has_event()) {
        log_d("no event -> sleeping");
        vTaskDelay(500/portTICK_PERIOD_MS);
    }
    taskENTER_CRITICAL(&stateMachine_model_event_spinlock);
    Event* ptr_event = m_ptr_event; // store it
    m_ptr_event = nullptr;          // clear it
    taskEXIT_CRITICAL(&stateMachine_model_event_spinlock);
    return ptr_event;               // return it
}

void Model::set_event(Event* ptr_event)  {
    log_d("set event: %s", ptr_event->m_name.c_str());
    taskENTER_CRITICAL(&stateMachine_model_event_spinlock);
    m_ptr_event = ptr_event;
    taskEXIT_CRITICAL(&stateMachine_model_event_spinlock);
}

bool Model::has_event() {
    taskENTER_CRITICAL(&stateMachine_model_event_spinlock);
    bool hasEvent = m_ptr_event != nullptr;
    taskEXIT_CRITICAL(&stateMachine_model_event_spinlock);

    return hasEvent;
}

class Transition {
    public:
        Transition(Event* trigger, State* source, State* destination) : m_ptr_trigger(trigger), m_ptr_source(source), m_ptr_destination(destination) {}
        Event* m_ptr_trigger;
        State* m_ptr_source;
        State* m_ptr_destination;
};

class StateMachine {
public:
    StateMachine(){
        log_d("default constructor StateMachine");
    }
    StateMachine(Model* model, Transition* transitions, uint8_t transitions_size, State* initial_state) : 
        m_ptr_model(model), m_ptr_transitions(transitions), m_transitions_size(transitions_size), m_ptr_state(initial_state) {
        log_d("parameter constructor StateMachine");
    }
    
    void start() {
        while (true) {

            log_d("StateMachine Model::run with state: %s", m_ptr_state->m_name.c_str());
            Event* ptr_new_event = m_ptr_model->run(m_ptr_state);
            log_d("model run finished, new_event: %s", ptr_new_event->m_name.c_str());

            bool found = false;
            for (uint8_t i = 0; i < m_transitions_size; i++) {

                if (m_ptr_transitions[i].m_ptr_trigger->equals(ptr_new_event) && m_ptr_transitions[i].m_ptr_source->equals(m_ptr_state)) {

                    log_d("new_event: %s, transition_source: %s, transition.destination: %s", 
                        ptr_new_event->m_name.c_str(), m_ptr_transitions[i].m_ptr_source->m_name.c_str(), m_ptr_transitions[i].m_ptr_destination->m_name.c_str());

                    m_ptr_state = m_ptr_transitions[i].m_ptr_destination;

                    Model* new_model = ptr_new_event->clear_new_model();
                    if (new_model != nullptr) {
                        log_d("setting new model");
                        m_ptr_model = new_model;
                    }

                    found = true;

                    break;
                }
            }
            if (!found) {
                log_d("No transition found for new_event: %s", ptr_new_event->m_name.c_str());
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