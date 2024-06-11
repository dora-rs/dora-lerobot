use dora_node_api::{
    arrow::array::Float32Array, dora_core::config::DataId, DoraNode, Event, IntoArrow,
};
use eyre::{Context, Result};
use rustypot::{device::xm, DynamixelSerialIO};
use std::time::Duration;

fn main() -> Result<()> {
    let (mut node, mut events) = DoraNode::init_from_env()?;
    let mut puppet_left_serial_port = serialport::new("/dev/ttyDXL_puppet_left", 1_000_000)
        .timeout(Duration::from_millis(2))
        .open()
        .expect("Failed to open port");
    let mut puppet_right_serial_port = serialport::new("/dev/ttyDXL_puppet_right", 1_000_000)
        .timeout(Duration::from_millis(2))
        .open()
        .expect("Failed to open port");
    let io = DynamixelSerialIO::v2();
    xm::sync_write_torque_enable(
        &io,
        puppet_left_serial_port.as_mut(),
        &[1, 2, 3, 4, 5, 6, 7, 8, 9],
        &[1; 9],
    )
    .expect("Communication error");
    xm::sync_write_torque_enable(
        &io,
        puppet_right_serial_port.as_mut(),
        &[1, 2, 3, 4, 5, 6, 7, 8, 9],
        &[1; 9],
    )
    .expect("Communication error");
    xm::sync_write_operating_mode(&io, puppet_left_serial_port.as_mut(), &[9], &[5])
        .expect("Communication error");
    xm::sync_write_operating_mode(&io, puppet_right_serial_port.as_mut(), &[9], &[5])
        .expect("Communication error");
    xm::sync_write_goal_position(&io, puppet_right_serial_port.as_mut(), &[9], &[3145])
        .expect("Communication error");
    let mut pos_right: Vec<f64> = vec![];
    while let Some(Event::Input {
        id,
        metadata: _,
        data,
    }) = events.recv()
    {
        match id.as_str() {
            "puppet_goal_position" => {
                let buffer: Float32Array = data
                    .to_data()
                    .try_into()
                    .context("Could not parse `puppet_goal_position` as float64")?;
                let target: &[f32] = buffer.values();
                let mut angular = target
                    .iter()
                    .map(|&x| xm::conv::radians_to_pos(x as f64))
                    .collect::<Vec<_>>();
                angular.insert(2, angular[1]);
                angular.insert(4, angular[3]);
                xm::sync_write_goal_position(
                    &io,
                    puppet_right_serial_port.as_mut(),
                    &[1, 2, 3, 4, 5, 6, 7, 8, 9],
                    &angular[..9],
                )
                .expect("Communication error");
            }
            "tick" => {
                let mut pos_left = xm::sync_read_present_position(
                    &io,
                    puppet_left_serial_port.as_mut(),
                    &[1, 2, 4, 6, 7, 8, 9],
                )
                .expect("Communication error");
                let tmp_pos_right = xm::sync_read_present_position(
                    &io,
                    puppet_right_serial_port.as_mut(),
                    &[1, 2, 4, 6, 7, 8, 9],
                )
                .expect("Communication error");
                // pos_left.extend_from_slice(&pos_right);

                pos_right = tmp_pos_right
                    .iter()
                    .map(|&x| xm::conv::pos_to_radians(x))
                    .collect();
                node.send_output(
                    DataId::from("puppet_position".to_owned()),
                    Default::default(),
                    pos_right.clone().into_arrow(),
                )?;
            }
            _ => todo!(),
        };
    }

    Ok(())
}
