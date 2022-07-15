
class Profile:
    children = []

    def __init__(self):
        Profile.children.append(self)

    @classmethod
    def find_profiles(cls):
        return cls.children


# def test_it():
#     class Player(Profile):
#         pass
#
#     class Flag(Profile):
#         pass
#
#     player = Player()
#     flag = Flag()
#
#     subclasses = Profile.find_profiles()
#     print(subclasses)
#
#
# # test_it()

