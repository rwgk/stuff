load("//:foo.bzl", "foo_binary")

print("BUILD file")

foo_binary(
    name = "bin1",
    username = "x",
)

foo_binary(
    name = "bin2",
    other = ":bin1",
    username = "y",
)
