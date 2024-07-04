# Dora pipeline Robots

AlexK Low Cost Robot is a low-cost robotic arm that can be teleoperated using a similar arm. This repository contains
the Dora pipeline to record episodes for LeRobot.

## Assembling

Check the [ASSEMBLING.md](ASSEMBLING.md) file for instructions on how to assemble the robot from scratch using the
provided parts from the [AlexK Low Cost Robot](https://github.com/AlexanderKoch-Koch/low_cost_robot)

## Installations

Check the [INSTALLATIONS.md](INSTALLATION.md) file for instructions on how to install the required software and
environment
to run the robot.

## Configuring

Check the [CONFIGURING.md](CONFIGURING.md) file for instructions on how to configure the robot to record episodes for
LeRobot and teleoperate the robot.

## Recording

It's probably better to check the [examples](#examples) below before trying to record episodes. It will give you a better
understanding of how Dora works.

Check the [RECORDING.md](RECORDING.md) file for instructions on how to record episodes for LeRobot.

## Examples

There are also some other example applications in the `graphs` folder. Have fun!

Here is a list of the available examples:

- `mono_teleop_real.yml`: A simple real teleoperation pipeline that allows you to control a follower arm using a leader
  arm. It
  does not record the episodes, so you don't need to have a camera.

You must configure the arms, retrieve the device port, and modify the file `mono_teleop_real.yml` to set the correct
environment variables. (e.g. `PORT`, `OFFSETS`, `DRIVE_MODES`)

```bash
cd dora-dora_lerobot/

# If you are using a custom environment, you will have to activate it before running the command
source [your_custom_env_bin]/activate

# If you followed the installation instructions, you can run the following command
source venv/bin/activate # On Linux
source venv/Scripts/activate # On Windows bash
venv\Scripts\activate.bat # On Windows cmd
venv\Scripts\activate.ps1 # On Windows PowerShell

dora up
dora start ./robots/alexk_lcr/graphs/mono_teleop_real.yml
```

[![](https://mermaid.ink/img/pako:eNqVUrFuwyAQ_RXEnMjt6qFD1bVTu4UIXc3ZRjpzFgZFVZR_L-A4TWtLVRng7vHe44A7y4YNylqK62iJT00PPoj3Z-WEoMZrQjDol8y6gH5kgoAL1DIlWaZM8aPzMPZCa23YQ1rEIQfHzL3fDXZAf50zqUSFJUQWVAWoBktkp-rx4aDULa4KD51RrkzbCrHfizES6ZEnGyy7BDxtXGipvvAXKkxiwdf6jSeYLX9bzOifBv-r_vu1Vx-SRR3DnSgVcfI2oP4Jr73kTqbzB7AmdcM5eysZehxQyTqFBluIFJRU7pKoEAO_fbpG1sFH3EnPsetl3QJNKYujScW8WEi_PdxQNDawf537rbTd5QtKFuLT?type=png)](https://mermaid.live/edit#pako:eNqVUrFuwyAQ_RXEnMjt6qFD1bVTu4UIXc3ZRjpzFgZFVZR_L-A4TWtLVRng7vHe44A7y4YNylqK62iJT00PPoj3Z-WEoMZrQjDol8y6gH5kgoAL1DIlWaZM8aPzMPZCa23YQ1rEIQfHzL3fDXZAf50zqUSFJUQWVAWoBktkp-rx4aDULa4KD51RrkzbCrHfizES6ZEnGyy7BDxtXGipvvAXKkxiwdf6jSeYLX9bzOifBv-r_vu1Vx-SRR3DnSgVcfI2oP4Jr73kTqbzB7AmdcM5eysZehxQyTqFBluIFJRU7pKoEAO_fbpG1sFH3EnPsetl3QJNKYujScW8WEi_PdxQNDawf537rbTd5QtKFuLT)

- `bi_teleop_real.yml`: A simple real tele operation pipeline that allows you to control two follower arm using two
  leader arm
  (left and right). It does not record the episodes, so you don't need to have a camera.

You must configure the arms, retrieve the device port, and modify the file `bi_teleop_real.yml` to set the correct
environment variables. (e.g. `PORT`, `OFFSETS`, `DRIVE_MODES`)

```bash
cd dora-dora_lerobot/

# If you are using a custom environment, you will have to activate it before running the command
source [your_custom_env_bin]/activate

# If you followed the installation instructions, you can run the following command
source venv/bin/activate # On Linux
source venv/Scripts/activate # On Windows bash
venv\Scripts\activate.bat # On Windows cmd
venv\Scripts\activate.ps1 # On Windows PowerShell

dora up
dora start ./robots/alexk_lcr/graphs/bi_teleop_real.yml
```

[![](https://mermaid.ink/img/pako:eNqlVMFugzAM_ZUo51ZsVw47TLvutN2aKcqIgUghQcFRNVX995lQ2oJgWzsOxrz4vdgmzoEXXgPPOTs9pfX7olYB2fuzcIzZIkgLJZJRGsIEMg4htN4qhAleeksql-BgqnouMGALCsPCRaKLn1VQbc2klNoHRS-2652PnnG9iqaBcLJ9UPJSFGM9IUtA1hhrTZc9PuyEOPtZigOnhUtmmcG2W9ZGa2XrO4PGOwKefmzRWEdijiTVsRFfUVrr7LDDXGxA_yZ1R1nz3zmX7emVV1d0ymkfDIKcwquqtyW1fpxu7_Yvx_C2fi-K3VPb8gD9p-VzXb7hlFGjjKbZP_T7CI41NCB4Tq6GUkWLggt3pFAV0b99uYLnGCJsePCxqnleKtvRV2w1pfRiFE1ic0ZBG_Thdbhd0iVz_AYd7pxh?type=png)](https://mermaid.live/edit#pako:eNqlVMFugzAM_ZUo51ZsVw47TLvutN2aKcqIgUghQcFRNVX995lQ2oJgWzsOxrz4vdgmzoEXXgPPOTs9pfX7olYB2fuzcIzZIkgLJZJRGsIEMg4htN4qhAleeksql-BgqnouMGALCsPCRaKLn1VQbc2klNoHRS-2652PnnG9iqaBcLJ9UPJSFGM9IUtA1hhrTZc9PuyEOPtZigOnhUtmmcG2W9ZGa2XrO4PGOwKefmzRWEdijiTVsRFfUVrr7LDDXGxA_yZ1R1nz3zmX7emVV1d0ymkfDIKcwquqtyW1fpxu7_Yvx_C2fi-K3VPb8gD9p-VzXb7hlFGjjKbZP_T7CI41NCB4Tq6GUkWLggt3pFAV0b99uYLnGCJsePCxqnleKtvRV2w1pfRiFE1ic0ZBG_Thdbhd0iVz_AYd7pxh)

- `mono_teleop_simu.yml`: A simple simulation tele operation pipeline that allows you to control a simulated follower
  arm using a leader arm. It does not record the episodes, so you don't need to have a camera.

You must configure the arms, retrieve the device port, and modify the file `mono_teleop_simu.yml` to set the correct
environment variables. (e.g. `PORT`, `OFFSETS`, `DRIVE_MODES`)

```bash
cd dora-dora_lerobot/


# If you are using a custom environment, you will have to activate it before running the command
source [your_custom_env_bin]/activate

# If you followed the installation instructions, you can run the following command
source venv/bin/activate # On Linux
source venv/Scripts/activate # On Windows bash
venv\Scripts\activate.bat # On Windows cmd
venv\Scripts\activate.ps1 # On Windows PowerShell

dora up
dora start ./robots/alexk_lcr/graphs/mono_teleop_simu.yml
```

[![](https://mermaid.ink/img/pako:eNp1UstuwyAQ_JUV50Rurz70UPXaU3sLEdqatY2KwcKgqIry711w4ubhcoDdYWZ3eBxF4zWJWsB5tNYfmh5DhM9X6QBsE5Ql1BQumXGRwugtRrpArbcsy5QpfXUBxx6UUtoH5AV2Odhn7vVuNAOF85xJJSosgCyoClANxlozVc9POymXuCo8clq6Mt26gO0Womm-AScYk7Vq9JOJxjveeFk50Jxl1UJk5Yw-au-Ov2a1lFpt_HdR_yuL9TXBXffM7TxedWHXh2AiqVv4sZbYCG47oNH88sdcW4rY00BS1BxqajHZKIV0J6Ziiv7jxzWijiHRRgSful7ULdqJszRqNvNmkF92WFDSJvrwPv-t8sVOv4Qz2jk?type=png)](https://mermaid.live/edit#pako:eNp1UstuwyAQ_JUV50Rurz70UPXaU3sLEdqatY2KwcKgqIry711w4ubhcoDdYWZ3eBxF4zWJWsB5tNYfmh5DhM9X6QBsE5Ql1BQumXGRwugtRrpArbcsy5QpfXUBxx6UUtoH5AV2Odhn7vVuNAOF85xJJSosgCyoClANxlozVc9POymXuCo8clq6Mt26gO0Womm-AScYk7Vq9JOJxjveeFk50Jxl1UJk5Yw-au-Ov2a1lFpt_HdR_yuL9TXBXffM7TxedWHXh2AiqVv4sZbYCG47oNH88sdcW4rY00BS1BxqajHZKIV0J6Ziiv7jxzWijiHRRgSful7ULdqJszRqNvNmkF92WFDSJvrwPv-t8sVOv4Qz2jk)

- `mono_teleop_real_and_simu.yml`: A simple real and simulation tele operation pipeline that allows you to control a
  simulated and real follower arm using a real leader arm. It does not record the episodes, so you don't need to have a
  camera.

```bash
cd dora-dora_lerobot/


# If you are using a custom environment, you will have to activate it before running the command
source [your_custom_env_bin]/activate

# If you followed the installation instructions, you can run the following command
source venv/bin/activate # On Linux
source venv/Scripts/activate # On Windows bash
venv\Scripts\activate.bat # On Windows cmd
venv\Scripts\activate.ps1 # On Windows PowerShell

dora up
dora start ./robots/alexk_lcr/graphs/mono_teleop_real_and_simu.yml
```

[![](https://mermaid.ink/img/pako:eNqdU8luwyAQ_RXEOZHbqw89VL321N5ChKjBMSqLxaKoivLvHXCM3IS0lX3Aw-O9YRbmhDvLBW4xuny9ssduYC6g92diEFKdo0owLty8kyYIN1rFgpih3iqQVSnUSx2veRfQx4-DY-OAKKXcOgY_tEvGPgmWp0FqUE1rImUrsxBKgiYDjZZKSd88PuwIKXaTecJwYvJSCQVttyjI7hMxj8aoFB2tl0FaAwdPlRLM4qQrVNAWpzf6StEml9cuJvRfDm5SgPQKf9mSWoXyvdVUf2lmEh0sW4gg4qOT0Oaf8D1fq3Muz2hdLn_Kc_fvqmrBrK5FVuMNhhg0kxxm75TuIDgMQguCWzC56FlUgWBizkBlMdi3L9PhNrgoNtjZeBhw2zPlYRdHDkG9SAbjogsquAzWvU7TnYf8_A1wbWmM?type=png)](https://mermaid.live/edit#pako:eNqdU8luwyAQ_RXEOZHbqw89VL321N5ChKjBMSqLxaKoivLvHXCM3IS0lX3Aw-O9YRbmhDvLBW4xuny9ssduYC6g92diEFKdo0owLty8kyYIN1rFgpih3iqQVSnUSx2veRfQx4-DY-OAKKXcOgY_tEvGPgmWp0FqUE1rImUrsxBKgiYDjZZKSd88PuwIKXaTecJwYvJSCQVttyjI7hMxj8aoFB2tl0FaAwdPlRLM4qQrVNAWpzf6StEml9cuJvRfDm5SgPQKf9mSWoXyvdVUf2lmEh0sW4gg4qOT0Oaf8D1fq3Muz2hdLn_Kc_fvqmrBrK5FVuMNhhg0kxxm75TuIDgMQguCWzC56FlUgWBizkBlMdi3L9PhNrgoNtjZeBhw2zPlYRdHDkG9SAbjogsquAzWvU7TnYf8_A1wbWmM)

## License

This library is licensed under the [Apache License 2.0](../../LICENSE).
