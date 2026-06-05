package autofounder.auth

# Default deny
default allow = false

# Allow if the user has admin or founder role
allow {
    input.role == "founder"
}

allow {
    input.role == "admin"
}

# Allow super_admin
allow {
    input.role == "super_admin"
}
