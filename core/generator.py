"""Локальний генератор. Випадковість надходить із системного CSPRNG."""
import secrets
import string

# Звичайні англійські слова. Вибір незалежний, із повтореннями.
# Вісім слів із цього набору дають понад 64 біти випадковості.
WORDS = tuple('''
acorn amber anchor apple apricot arch arrow ash atlas autumn
badge bamboo banana barley barn basin basket bay beach bean
bear beech bell berry birch bird bison blade blanket bloom
boat bolt book boot bottle boulder bowl branch brass bread
brick bridge brook brush bucket bud buffalo button cabin cactus
candle canyon cape carrot castle cedar celery chalk cherry chest
chick circle clay cliff cloud clover coast cocoa coconut coffee
comet coral cotton crane creek crown crystal cube cup curtain
daisy dawn deer delta desert diamond dock dolphin door dove
dragon drum dune eagle earth elm ember emerald engine falcon
farm feather fern field fig finch fire fir flag flame
flint flour flower flute fog forest fork fossil fountain fox
frame frost fruit garden gate gem ginger glacier glass globe
goat gold goose grain grape grass gravel grove gull harbor
hare harp hawk hazel hedge heron hill honey horn horse
house ice iris island ivory ivy jacket jade jar jasmine
jay jewel jug juniper kettle key kite kiwi lake lamb
lamp lantern lark laurel leaf lemon lens lettuce lilac lily
lime linen lion lizard loaf log lotus maple marble marsh
meadow melon metal meteor mint mirror mist moon moss moth
mountain mug mushroom needle nest nettle night north nut oak
oar ocean olive onion opal orange orchid otter owl oyster
palm panda paper peach peak pear pebble pecan pepper petal
pine pipe planet plum pond poplar poppy potato pot prairie
prism pumpkin quartz quill rabbit rain raven reed reef ribbon
rice ridge river robin rock root rope rose ruby sage
sail salmon salt sand satin scarf sea seal seed shell
shield shore silver slate slope snail snow soap sparrow spice
spoon spring spruce square squirrel star stone stream string sugar
summit sun swan table tea temple thorn thread thyme tiger
timber tin toast tomato torch tower trail tree trout tulip
tunnel turtle valley velvet vine violet walnut wave wax wheat
wheel willow wind wing winter wolf wood wool wren yard
yarn yellow yew zebra zinc zipper almond antelope apron attic
avocado bakery balcony bat beetle biscuit bonnet breeze brooch bronze
canary canvas caramel cat chisel cinnamon coconut compass copper cove
cranberry daffodil dam dolphin duck elm fabric ferry fiddle foxglove
galaxy garlic gazelle gooseberry granite hammock hazelnut helmet hickory iceberg
indigo ink lagoon lapis lava lavender magnet mango molasses mulberry
nectar notebook orchard parrot pastry pelican penguin plateau plumage pottery
radish rainbow raisin ripple saddle sapphire sequoia skylark snowdrop sparrowhawk
stork straw sycamore tangerine teak thistle thunder turnip violin water
'''.split())
WORDS = tuple(dict.fromkeys(WORDS))


def generate_password(length=20, symbols=True):
    if not 12 <= length <= 64:
        raise ValueError('Password length must be between 12 and 64')
    groups = [string.ascii_lowercase, string.ascii_uppercase, string.digits]
    if symbols:
        groups.append('!@#$%&*+-=?')
    alphabet = ''.join(groups)
    while True:
        value = ''.join(secrets.choice(alphabet) for _ in range(length))
        if all(any(character in group for character in value) for group in groups):
            return value


def generate_passphrase(count=8):
    if not 6 <= count <= 10:
        raise ValueError('Word count must be between 6 and 10')
    return '-'.join(secrets.choice(WORDS) for _ in range(count))
