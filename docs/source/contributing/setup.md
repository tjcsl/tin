(dev-setup)=

# Setting up a development environment

To begin with, you will need to have [git](https://git-scm.com/) installed on your computer.
You will also need a GitHub account.

First, [fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo#forking-a-repository)
tin. Then you can clone tin onto your computer with

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/tin
```

From here, you can either use a local setup, or use Docker. Check out the
relevant sections.

## Docker

If you prefer, you can run the development setup with [Docker](https://www.docker.com/). To do so,
`cd` into the project directory and run:

```
docker compose build
docker compose up
```

To create testing users and apply migrations, run the below command in a separate terminal:

```
./scripts/docker_setup.sh
```

## Local Setup

To set up your environment locally, you will need to install the following:

- [uv](https://docs.astral.sh/uv/)

Then, run these commands:

```
uv run manage.py migrate
uv run manage.py create_debug_users
```

Now you're all set! Try running the development server

```bash
uv run manage.py runserver
```

Head on over to [http://127.0.0.1:8000](http://127.0.0.1:8000), and login
as `admin` and the password you just entered.

In order to actually submit code, there are some more steps. First,
you'll need to install [redis](https://redis.io/download).

You'll also need to start the celery worker. This can be done
by running the following command in a separate terminal:

```
uv run celery -A tin worker --loglevel=info
```

## Final Steps

After that, you'll want to create a course and an assignment in the course.
After saving the assignment, you can hit "Upload grader" to add a grader -
the simplest example of a grader is located in `scripts/sample_grader.py`.

Now you can try making a submission, and as long as your submission doesn't throw an error you
should get a 100%! Congrats on your brand new 5.0 GPA!

## Testing the sandbox (Vagrant VM)

The sandboxing that isolates student code (firejail + bubblewrap) does **not**
engage under the Docker dev setup: Docker's unprivileged containers make firejail
a no-op, so you cannot faithfully test sandbox behaviour there. For in-depth
security testing — e.g. verifying that a submission cannot read sibling
submissions, reach the host filesystem, or otherwise escape the sandbox — use the
Vagrant VM, which runs Tin natively on a real Linux kernel with firejail and
bubblewrap actually enforcing.

You will need [Vagrant](https://developer.hashicorp.com/vagrant) and
[VirtualBox](https://www.virtualbox.org/). Then, from the repository root:

```bash
cd vagrant
vagrant up
```

The first `vagrant up` provisions firejail, bubblewrap, a JDK, redis, and `uv`,
copies Tin to a native path, and starts it as systemd services. Tin is then served
at <http://localhost:8000> — log in via `/password-login/` as `admin`, `teacher`,
or `student` (password `jasongrace`). Useful commands:

```bash
vagrant ssh          # shell into the VM (Tin lives in /home/vagrant/tin)
vagrant provision    # re-sync code + restart services after editing on the host
vagrant halt         # stop the VM        (state is preserved)
vagrant destroy -f   # delete the VM
journalctl -u tin-web -u tin-celery -f    # (inside the VM) follow logs
```

```{note}
On Windows, if Docker Desktop / WSL2 / Hyper-V is active, VirtualBox runs in a
slow compatibility mode (or fails with VT-x errors); quit Docker Desktop, and if
needed disable Hyper-V, for full-speed VirtualBox. If Vagrant can't find
`VBoxManage`, add VirtualBox's install directory to your `PATH`.
```
