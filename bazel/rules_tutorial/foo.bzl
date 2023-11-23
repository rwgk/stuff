def _foo_binary_impl(ctx):
    print("analyzing", ctx.label)
    if ctx.attr.other != None:
        print("ctx.attr.other.files", ctx.attr.other.files)
    print("ctx.file.other", ctx.file.other)
    if ctx.file.other != None:
        print("dir(ctx.file.other)", dir(ctx.file.other))
        print("ctx.file.other.basename", ctx.file.other.basename)
        print("ctx.file.other.dirname", ctx.file.other.dirname)
        print("ctx.file.other.extension", ctx.file.other.extension)
        print("ctx.file.other.is_directory", ctx.file.other.is_directory)
        print("ctx.file.other.is_source", ctx.file.other.is_source)
        print("ctx.file.other.owner", ctx.file.other.owner)
        print("ctx.file.other.path", ctx.file.other.path)
        print("ctx.file.other.root", ctx.file.other.root)
        print("ctx.file.other.short_path", ctx.file.other.short_path)
        # print("ctx.file.other.tree_relative_path", ctx.file.other.tree_relative_path)

    out = ctx.actions.declare_file(ctx.label.name)
    ctx.actions.write(
        output = out,
        content = "Hello, %s!\n" % ctx.attr.username,
    )
    return [DefaultInfo(files = depset([out]))]

foo_binary = rule(
    implementation = _foo_binary_impl,
    attrs = {
        "username": attr.string(),
        "other": attr.label(allow_single_file = True),
    },
)

print("bzl file evaluation")
