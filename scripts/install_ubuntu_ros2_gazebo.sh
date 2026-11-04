#!/usr/bin/env bash
# Installation complète : Ubuntu 24.04 LTS + ROS 2 Jazzy Jalisco + Gazebo Harmonic + outils.
# Usage : bash scripts/install_ubuntu_ros2_gazebo.sh      (durée ~15-25 min, connexion Internet requise)
set -euo pipefail

if ! grep -q "24.04" /etc/os-release; then
  echo "⚠  Ubuntu 24.04 LTS requis (détecté : $(. /etc/os-release; echo "$PRETTY_NAME"))"; exit 1
fi

echo "==> 1/6 Locale UTF-8 et dépôts"
sudo apt update && sudo apt install -y locales software-properties-common curl gnupg lsb-release git
sudo locale-gen en_US en_US.UTF-8 && sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
sudo add-apt-repository -y universe

echo "==> 2/6 Dépôt ROS 2"
if [ ! -f /usr/share/keyrings/ros-archive-keyring.gpg ]; then
  sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
fi
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update

echo "==> 3/6 ROS 2 Jazzy + outils de build"
sudo apt install -y ros-jazzy-desktop ros-dev-tools python3-colcon-common-extensions python3-rosdep

echo "==> 4/6 Gazebo Harmonic + ponts ROS<->Gazebo"
sudo apt install -y ros-jazzy-ros-gz ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge ros-jazzy-ros-gz-interfaces

echo "==> 5/6 Python / OpenCV / tests"
sudo apt install -y python3-numpy python3-opencv python3-pytest

echo "==> 6/6 rosdep + environnement"
sudo rosdep init 2>/dev/null || true
rosdep update
grep -q "/opt/ros/jazzy/setup.bash" ~/.bashrc || echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
echo "✅ Installation terminée. Ouvrez un NOUVEAU terminal puis : bash scripts/build.sh"
echo "   Vérification : ros2 --version ; gz sim --version"
