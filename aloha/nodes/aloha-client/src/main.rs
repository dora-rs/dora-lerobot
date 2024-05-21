use dora_node_api::{
    arrow::array::Float64Array, dora_core::config::DataId, DoraNode, Event, IntoArrow,
};
use eyre::{Context, Result};
use rustypot::{device::xm, DynamixelSerialIO};
use std::time::Duration;

fn main() -> Result<()> {
    let (mut node, mut events) = DoraNode::init_from_env()?;
    let mut puppet_serial_port = serialport::new("/dev/ttyDXL_puppet_right", 1_000_000)
        .timeout(Duration::from_millis(2))
        .open()
        .expect("Failed to open port");
    let io = DynamixelSerialIO::v2();
    xm::sync_write_torque_enable(
        &io,
        puppet_serial_port.as_mut(),
        &[1, 2, 3, 4, 5, 6, 7, 8, 9],
        &[1; 9],
    )
    .expect("Communication error");

    while let Some(Event::Input {
        id,
        metadata: _,
        data,
    }) = events.recv()
    {
        match id.as_str() {
            "puppet_goal_position" => {
                let buffer: Float64Array = data
                    .to_data()
                    .try_into()
                    .context("Could not parse `puppet_goal_position` as float64")?;
                let target: &[f64] = buffer.values();
                let mut angular = target
                    .iter()
                    .map(|&x| xm::conv::radians_to_pos(x))
                    .collect::<Vec<_>>();
                angular.insert(2, angular[1]);
                angular.insert(4, angular[3]);
                xm::sync_write_goal_position(
                    &io,
                    puppet_serial_port.as_mut(),
                    &[1, 2, 3, 4, 5, 6, 7, 8, 9],
                    &angular,
                )
                .expect("Communication error");
            }
            "tick" => {
                let pos = xm::sync_read_present_position(
                    &io,
                    puppet_serial_port.as_mut(),
                    &[1, 2, 4, 6, 7, 8, 9],
                )
                .expect("Communication error");
                node.send_output(
                    DataId::from("puppet_position".to_owned()),
                    Default::default(),
                    pos.into_arrow(),
                )?;
            }
            _ => todo!(),
        };
    }

    Ok(())
}
