

class Team
{
public:
  Team(const uint16_t &color, const std::string &name) : m_color(color), m_name(name)
  {}
  
  uint16_t color() const {
    return m_color;
  }

  std::string name() const {
    return m_name;
  }

private:
  const uint16_t m_color;
  const std::string m_name;
};
